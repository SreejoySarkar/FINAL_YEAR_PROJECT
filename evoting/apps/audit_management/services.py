from django.db import connection, transaction
from django.utils import timezone

from evoting_crypto import hashing

from .models import AuditLog

GENESIS_HASH = "0" * 64
_ADVISORY_LOCK_ID = 7_340_001


def _event_hash(previous_hash, actor, election_id, action, details, created_at) -> str:
    return hashing.sha256_hex(
        "evoting/audit/v1",
        previous_hash,
        actor,
        "" if election_id is None else str(election_id),
        action,
        hashing.canonical_json(details),
        created_at.isoformat(),
    )


def log_event(action: str, *, election=None, actor: str = "system", details: dict | None = None) -> AuditLog:
    """Append one event. A PostgreSQL advisory lock serialises writers so the chain never forks."""
    details = details or {}
    with transaction.atomic():
        if connection.vendor == "postgresql":
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_ADVISORY_LOCK_ID])
        last = AuditLog.objects.order_by("-id").first()
        previous = last.event_hash if last else GENESIS_HASH
        now = timezone.now()
        election_id = election.pk if election is not None else None
        digest = _event_hash(previous, actor, election_id, action, details, now)
        return AuditLog.objects.create(
            actor_reference=actor,
            election=election,
            action=action,
            details=details,
            previous_hash=previous,
            event_hash=digest,
            created_at=now,
        )


def verify_chain() -> dict:
    expected_prev, count, broken_at = GENESIS_HASH, 0, None
    for row in AuditLog.objects.order_by("id").iterator(chunk_size=1000):
        count += 1
        recomputed = _event_hash(row.previous_hash, row.actor_reference, row.election_id, row.action, row.details, row.created_at)
        if row.previous_hash != expected_prev or row.event_hash != recomputed:
            broken_at = row.id
            break
        expected_prev = row.event_hash
    return {"ok": broken_at is None, "events_checked": count, "first_broken_id": broken_at, "head_hash": expected_prev}
