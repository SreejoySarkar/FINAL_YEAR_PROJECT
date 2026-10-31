"""Optional, dependency-free anomaly detection over the audit log (rules + z-scores).
It only READS audit metadata - never ballots - and only advises; it never blocks anything."""
from collections import Counter
from statistics import mean, pstdev

from apps.anonymous_storage.models import AnonymousBallot
from apps.audit_management.models import AuditLog
from apps.anonymous_authorization.models import AuthorizationCredential


def _burst(buckets: Counter, label: str, min_events: int = 20, z_limit: float = 3.0):
    if len(buckets) < 5:
        return None
    values = list(buckets.values())
    mu, sd = mean(values), pstdev(values) or 1.0
    minute, peak = max(buckets.items(), key=lambda kv: kv[1])
    if peak >= min_events and (peak - mu) / sd >= z_limit:
        return {"severity": "medium", "type": f"{label}_BURST",
                "message": f"{peak} {label.lower()} events in one minute ({minute:%H:%M}) vs. an average of {mu:.1f}."}
    return None


def analyze_election(election) -> dict:
    findings = []
    events = AuditLog.objects.filter(election=election).values_list("action", "created_at")
    per_action: dict[str, Counter] = {}
    totals = Counter()
    for action, created in events.iterator():
        totals[action] += 1
        per_action.setdefault(action, Counter())[created.replace(second=0, microsecond=0)] += 1
    for action in ("VOTE_REJECTED", "VOTE_ACCEPTED"):
        if action in per_action and (b := _burst(per_action[action], action)):
            findings.append(b)
    accepted, rejected = totals["VOTE_ACCEPTED"], totals["VOTE_REJECTED"]
    if accepted + rejected >= 10 and rejected / (accepted + rejected) > 0.2:
        findings.append({"severity": "high", "type": "HIGH_REJECTION_RATE",
                         "message": f"{rejected} of {accepted + rejected} submissions were rejected."})
    qr_fail = AuditLog.objects.filter(action="QR_VALIDATION_FAILED").count()
    if qr_fail >= 25:
        findings.append({"severity": "medium", "type": "QR_GUESSING",
                         "message": f"{qr_fail} failed QR validations (possible token guessing)."})
    creds = AuthorizationCredential.objects.filter(election=election, status="ACTIVE").count()
    ballots = AnonymousBallot.objects.filter(election=election).count()
    if ballots > creds:
        findings.append({"severity": "critical", "type": "MORE_BALLOTS_THAN_CREDENTIALS",
                         "message": f"{ballots} ballots exist but only {creds} credentials were issued."})
    summary = ("No anomalies detected." if not findings else
               f"{len(findings)} potential issue(s); highest severity: " +
               max((f['severity'] for f in findings), key=["medium", "high", "critical"].index) + ".")
    return {"election_id": str(election.pk), "events_analyzed": sum(totals.values()), "summary": summary, "findings": findings}
