import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Vote, CalendarDays, ChevronRight, CheckCheck, Lock, UserCheck, RefreshCw } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, StatusBadge, Alert, Toast, useToast, EmptyState, initials, avatarColor } from "../components/ui";
import PageLoading from "../components/Loading";
import { useAuth } from "../context/AuthContext";
import { listMyElections } from "../services/votingService";
import { formatDate } from "../services/electionService";
import { friendlyMessage } from "../services/api";

export default function VoterDashboard() {
  const { user } = useAuth();
  const [elections, setElections] = useState(null);
  const [error, setError] = useState(null);
  const { toast, show, dismiss } = useToast();

  const load = async () => {
    setError(null);
    try {
      // The backend decides which elections this voter may see — we render
      // exactly what it returns, nothing else.
      setElections(await listMyElections());
    } catch (err) {
      setError(friendlyMessage(err));
    }
  };

  useEffect(() => { load(); }, []);

  const ctaFor = (e) => {
    if (e.status === "active") {
      if (!e.eligible) return { label: "Not eligible", icon: Lock, kind: "none" };
      if (e.has_voted) return { label: "Ballot submitted", icon: CheckCheck, kind: "done" };
      return { label: "Start voting", icon: ChevronRight, kind: "go", to: `/vote/qr/${e.id}` };
    }
    if (e.status === "upcoming") return { label: `Opens ${formatDate(e.starts_at)}`, icon: CalendarDays, kind: "none" };
    if (e.status === "closed") return { label: "Election closed", icon: Lock, kind: "none" };
    return { label: "Unavailable", icon: Lock, kind: "none" };
  };

  return (
    <DashboardLayout
      crumb="Voter"
      title="My Elections"
      actions={
        <button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={14} className="me-1" /> Refresh</button>
      }
    >
      {/* welcome + voter info */}
      <div className="card mb-4" style={{ background: "linear-gradient(120deg, var(--navy-950), var(--navy-900) 55%, #0d2445)", border: "none" }}>
        <div className="card-body d-flex align-items-center gap-3 flex-wrap" style={{ padding: "1.3rem 1.5rem" }}>
          <span className="avatar avatar-lg" style={{ background: avatarColor(user?.name || "") }}>{initials(user?.name || "")}</span>
          <div style={{ minWidth: 0 }}>
            <div className="eyebrow" style={{ color: "#45e0a2" }}>Voter portal</div>
            <h3 className="mb-0" style={{ color: "#fff", fontSize: "1.3rem" }}>Welcome, {user?.name || "Voter"}</h3>
            <div className="d-flex flex-wrap gap-3 mt-1" style={{ fontSize: "0.85rem", color: "#9fb2cb", fontWeight: 600 }}>
              {user?.voter_id && <span className="d-flex align-items-center gap-1"><UserCheck size={14} className="text-green-accent" /> Voter ID: {user.voter_id}</span>}
              <span>{user?.email || ""}</span>
            </div>
          </div>
          <div className="ms-auto text-end" style={{ fontSize: "0.82rem", color: "#9fb2cb" }}>
            <div className="fw-bold" style={{ color: "#fff", fontFamily: "var(--font-display)", fontSize: "1.4rem" }}>{elections ? elections.filter((e) => e.status === "active" && !e.has_voted).length : "…"}</div>
            elections open for you
          </div>
        </div>
      </div>

      <PageHeader title="Available elections" subtitle="Only elections the backend has made available to your voter record appear here.">
        {elections && <span className="badge badge-navy">{elections.length} elections</span>}
      </PageHeader>

      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {elections === null ? (
        <div className="card"><PageLoading label="Checking your elections…" /></div>
      ) : elections.length === 0 ? (
        <div className="card">
          <EmptyState icon={Vote} title="No elections available" text="There are currently no elections available for your voter record." />
        </div>
      ) : (
        <div className="row g-3">
          {elections.map((e) => {
            const cta = ctaFor(e);
            const Icon = cta.icon;
            return (
              <div className="col-12 col-lg-6" key={e.id}>
                <div className="election-card h-100">
                  <div className="top">
                    <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
                      <StatusBadge status={e.status} />
                      {!e.eligible && e.status === "active" && <span className="badge badge-red">Not eligible</span>}
                      {e.has_voted && <span className="badge badge-green"><CheckCheck size={11} className="me-1" />Voted</span>}
                    </div>
                    <h5 style={{ fontWeight: 700, fontSize: "1.05rem" }}>{e.title}</h5>
                    {e.description && <p className="text-soft" style={{ fontSize: "0.86rem", lineHeight: 1.55 }}>{e.description}</p>}
                    <div className="d-flex flex-column gap-1" style={{ fontSize: "0.82rem", color: "var(--ink-soft)" }}>
                      <span className="d-flex align-items-center gap-2"><CalendarDays size={14} className="text-faint" /> {formatDate(e.starts_at)} → {formatDate(e.ends_at)}</span>
                      <span className="d-flex align-items-center gap-2"><Vote size={14} className="text-faint" /> {e.candidates_count ?? "—"} candidates · one ballot per voter</span>
                    </div>
                  </div>
                  <div className="foot">
                    <span className="text-faint" style={{ fontSize: "0.8rem" }}>
                      {e.status === "active" ? (e.has_voted ? "Thank you — your ballot is sealed." : e.eligible ? "Ready when you are." : "Contact the election administrator.") : e.status === "upcoming" ? "Voting opens soon." : "No further action needed."}
                    </span>
                    {cta.kind === "go" ? (
                      <Link to={cta.to} className="btn btn-accent btn-sm">
                        {cta.label} <Icon size={14} className="ms-1" />
                      </Link>
                    ) : (
                      <span className={`badge ${cta.kind === "done" ? "badge-green" : "badge-muted"}`} style={{ fontSize: "0.74rem" }}>
                        <Icon size={11} className="me-1" /> {cta.label}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
