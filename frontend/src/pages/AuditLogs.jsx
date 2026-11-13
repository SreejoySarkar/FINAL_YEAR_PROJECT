import { useEffect, useState, useCallback } from "react";
import { ScrollText, RefreshCw } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, Alert, Toast, useToast, EmptyState } from "../components/ui";
import PageLoading from "../components/Loading";
import { getAuditLogs } from "../services/resultsService";
import { friendlyMessage } from "../services/api";
import { formatDate } from "../services/electionService";

const CATEGORIES = [
  ["all", "All"],
  ["auth", "Authentication"],
  ["election", "Elections"],
  ["qr", "QR access"],
  ["vote", "Ballots"],
  ["candidate", "Candidates"],
  ["voter", "Voters"],
  ["results", "Results"],
];

export default function AuditLogs() {
  const [logs, setLogs] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const { toast, show, dismiss } = useToast();

  const load = useCallback(async () => {
    setError(null);
    try {
      setLogs(await getAuditLogs());
    } catch (err) {
      setError(friendlyMessage(err));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visible = (logs || []).filter((l) => filter === "all" || l.category === filter);

  return (
    <DashboardLayout
      crumb="Admin / Audit"
      title="Audit Logs"
      actions={<button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={14} className="me-1" /> Refresh</button>}
    >
      <PageHeader title="Append-only activity trail" subtitle="Every significant action — logins, token issuance, ballots and result publication — is recorded by the backend. Entries are never edited or deleted.">
        <div className="d-flex gap-1 flex-wrap">
          {CATEGORIES.map(([key, label]) => (
            <button
              key={key}
              className={`btn btn-sm ${filter === key ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </PageHeader>

      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {logs === null ? (
        <div className="card"><PageLoading label="Loading audit trail…" /></div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table align-middle">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Actor</th>
                  <th>Category</th>
                  <th>Action</th>
                  <th>Detail</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {visible.length === 0 && (
                  <tr>
                    <td colSpan={6}>
                      <EmptyState icon={ScrollText} title="No entries" text="No audit entries match this filter yet." />
                    </td>
                  </tr>
                )}
                {visible.map((a) => (
                  <tr key={a.id}>
                    <td className="text-soft text-nowrap" style={{ fontSize: "0.84rem" }}>{formatDate(a.at)}</td>
                    <td style={{ fontSize: "0.88rem", whiteSpace: "nowrap" }}>{a.actor}</td>
                    <td><span className="badge badge-navy">{(CATEGORIES.find((c) => c[0] === a.category) || [null, a.category])[1]}</span></td>
                    <td style={{ fontFamily: "var(--font-display)", fontSize: "0.82rem", fontWeight: 700, letterSpacing: "0.02em" }}>{a.action}</td>
                    <td className="text-soft" style={{ fontSize: "0.85rem", maxWidth: 420 }}>{a.detail}</td>
                    <td>
                      {a.status === "ok" ? <span className="badge badge-green">OK</span> : <span className="badge badge-red">{a.status}</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
