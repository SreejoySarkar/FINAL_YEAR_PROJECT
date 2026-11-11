import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Vote, Radio, Users, UserSquare2, CheckSquare, Plus, QrCode, ScrollText, Activity } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { StatCard, StatusBadge, Alert, Toast, useToast, EmptyState } from "../components/ui";
import PageLoading from "../components/Loading";
import { request, API_PATHS, friendlyMessage } from "../services/api";
import { getAuditLogs } from "../services/resultsService";
import { listElections } from "../services/electionService";
import { formatDate } from "../services/electionService";

const CATEGORY_LABEL = { auth: "Authentication", election: "Election", qr: "QR Access", vote: "Ballot", results: "Results", candidate: "Candidate" };

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [elections, setElections] = useState(null);
  const [audit, setAudit] = useState(null);
  const [error, setError] = useState(null);
  const { toast, show, dismiss } = useToast();

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [s, e, a] = await Promise.all([
          request(API_PATHS.adminStats),
          listElections(),
          getAuditLogs(),
        ]);
        if (!alive) return;
        setStats(s);
        setElections(e);
        setAudit(a);
      } catch (err) {
        if (alive) setError(friendlyMessage(err));
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  if (error) {
    return (
      <DashboardLayout crumb="Admin" title="Dashboard">
        <Alert variant="danger">{error}</Alert>
      </DashboardLayout>
    );
  }
  if (!stats) return <DashboardLayout crumb="Admin" title="Dashboard"><PageLoading label="Loading dashboard…" /></DashboardLayout>;

  const active = elections?.filter((e) => e.status === "active") || [];

  return (
    <DashboardLayout
      crumb="Admin"
      title="Dashboard"
      actions={
        <>
          <Link to="/admin/elections" className="btn btn-ghost btn-sm">Manage elections</Link>
          <Link to="/admin/qr" className="btn btn-primary btn-sm">
            <QrCode size={14} className="me-1" /> New QR token
          </Link>
        </>
      }
    >
      {/* KPI row — all figures come from the backend stats endpoint */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-xl"><StatCard icon={Vote} label="Total elections" value={stats.elections_total} tone="navy" /></div>
        <div className="col-6 col-xl"><StatCard icon={Radio} label="Active elections" value={stats.elections_active} tone="green" /></div>
        <div className="col-6 col-xl"><StatCard icon={Users} label="Registered voters" value={stats.voters_total} tone="navy" /></div>
        <div className="col-6 col-xl"><StatCard icon={UserSquare2} label="Total candidates" value={stats.candidates_total} tone="warn" /></div>
        <div className="col-6 col-xl"><StatCard icon={CheckSquare} label="Votes submitted" value={stats.votes_total} tone="green" hint="Confirmed ballots across all elections" /></div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-lg-7">
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between">
              <span className="d-flex align-items-center gap-2"><Activity size={16} /> Active elections</span>
              <Link to="/admin/elections" style={{ fontSize: "0.82rem", fontWeight: 700 }}>Manage all →</Link>
            </div>
            <div className="card-body pt-3">
              {active.length === 0 ? (
                <EmptyState icon={Vote} title="No elections running" text="Create an election and set its status to active to start accepting ballots.">
                  <Link to="/admin/elections" className="btn btn-primary btn-sm"><Plus size={14} className="me-1" /> New election</Link>
                </EmptyState>
              ) : (
                <div className="d-grid gap-3">
                  {active.map((e) => (
                    <div key={e.id} className="d-flex align-items-center gap-3 p-3" style={{ border: "1px solid var(--line)", borderRadius: "var(--radius-md)", background: "#fafcfe" }}>
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div className="fw-bold" style={{ fontFamily: "var(--font-display)" }}>{e.title}</div>
                        <div className="text-faint" style={{ fontSize: "0.8rem" }}>
                          Closes {formatDate(e.ends_at)} · {e.candidates_count ?? "—"} candidates · {e.votes_cast ?? 0} ballots
                        </div>
                      </div>
                      <StatusBadge status="active" />
                      <Link to="/admin/elections" className="btn btn-ghost btn-sm flex-none">View</Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-5">
          <div className="card">
            <div className="card-header d-flex align-items-center justify-content-between">
              <span className="d-flex align-items-center gap-2"><ScrollText size={16} /> Recent activity</span>
              <Link to="/admin/audit" style={{ fontSize: "0.82rem", fontWeight: 700 }}>Full audit log →</Link>
            </div>
            <div className="card-body pt-3">
              {!audit ? (
                <PageLoading />
              ) : (
                <div className="d-grid gap-3">
                  {audit.slice(0, 6).map((a) => (
                    <div className="audit-item" key={a.id}>
                      <span className="audit-dot" />
                      <div className="d-flex justify-content-between gap-2">
                        <span style={{ fontWeight: 700, fontSize: "0.86rem" }}>{CATEGORY_LABEL[a.category] || a.action}</span>
                        <span className="text-faint" style={{ fontSize: "0.74rem", whiteSpace: "nowrap" }}>{formatDate(a.at)}</span>
                      </div>
                      <div className="text-soft" style={{ fontSize: "0.82rem", lineHeight: 1.45 }}>{a.detail}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
