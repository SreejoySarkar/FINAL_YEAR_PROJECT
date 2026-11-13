import { useEffect, useState, useCallback } from "react";
import { BarChart3, Lock, ShieldCheck, FileCheck2, RefreshCw } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, StatusBadge, Alert, Toast, useToast } from "../components/ui";
import PageLoading from "../components/Loading";
import { listElections } from "../services/electionService";
import { getResults } from "../services/resultsService";
import { friendlyMessage, DEMO_MODE } from "../services/api";

const CHART_COLORS = ["#17b877", "#163a6d", "#45e0a2", "#0a1b33", "#cf8a1b", "#7c8aa0"];

export default function Results() {
  const [elections, setElections] = useState([]);
  const [selected, setSelected] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const { toast, show, dismiss } = useToast();

  const loadElections = useCallback(async () => {
    try {
      const els = await listElections();
      setElections(els);
      // Preselect the first election with published results, else the first closed one, else the first.
      const pref = els.find((e) => e.status === "closed" && e.results_published) || els[0];
      if (pref && !selected) setSelected(String(pref.id));
      return els;
    } catch (err) {
      setError(friendlyMessage(err));
      return [];
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadElections(); }, [loadElections]);

  useEffect(() => {
    if (!selected) return;
    let alive = true;
    setResults(null);
    setError(null);
    getResults(Number(selected))
      .then((r) => alive && setResults(r))
      .catch((err) => alive && setError(friendlyMessage(err)));
    return () => { alive = false; };
  }, [selected]);

  const published = results?.results_published && results?.results_verified;
  const barData = published ? results.candidates.map((c) => ({ name: c.name.length > 18 ? c.name.slice(0, 17) + "…" : c.name, votes: c.votes })) : [];
  const pieData = published ? results.candidates.map((c) => ({ name: c.name, value: c.votes })) : [];

  return (
    <DashboardLayout
      crumb="Admin / Results"
      title="Election Results"
      actions={<button className="btn btn-ghost btn-sm" onClick={loadElections}><RefreshCw size={14} className="me-1" /> Refresh</button>}
    >
      <PageHeader
        title="Official results"
        subtitle="Only the backend can publish results. Figures appear here when the election is closed, verified against the audit trail and marked as published."
      >
        <select className="form-select form-select-sm" style={{ width: "auto", minWidth: 260 }} value={selected} onChange={(e) => setSelected(e.target.value)} aria-label="Select election">
          {elections.map((e) => (
            <option key={e.id} value={e.id}>{e.title} ({e.status})</option>
          ))}
        </select>
      </PageHeader>

      {DEMO_MODE && published && (
        <Alert variant="warning" className="mb-3">
          <span style={{ fontSize: "0.84rem" }}>These are <strong>sample figures</strong> from demo mode — with your Django backend connected, this page shows only officially published results.</span>
        </Alert>
      )}
      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {!results && !error ? (
        <div className="card"><PageLoading label="Loading results…" /></div>
      ) : !published ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <div className="mx-auto mb-3" style={{ width: 66, height: 66, borderRadius: 18, background: "var(--navy-100)", color: "var(--navy-800)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Lock size={28} />
            </div>
            <h5 style={{ fontWeight: 700 }}>Results not yet published</h5>
            <p className="text-soft mx-auto" style={{ maxWidth: "52ch", fontSize: "0.92rem", lineHeight: 1.65 }}>
              {results?.audit_summary || "The backend has not marked this election's results as verified and published. Official figures will appear here automatically once it does."}
            </p>
            {results && (
              <div className="d-flex justify-content-center gap-2 flex-wrap">
                <StatusBadge status={results.status} />
                <span className={`badge ${results.results_published ? "badge-green" : "badge-muted"}`}>Published: {results.results_published ? "yes" : "no"}</span>
                <span className={`badge ${results.results_verified ? "badge-green" : "badge-muted"}`}>Verified: {results.results_verified ? "yes" : "no"}</span>
              </div>
            )}
          </div>
        </div>
      ) : (
        <>
          <div className="row g-3 mb-3">
            <div className="col-6 col-md-3">
              <div className="kpi-card"><div style={{ minWidth: 0 }}><div className="small-caps">Election</div><div style={{ fontWeight: 800, fontFamily: "var(--font-display)", fontSize: "1.02rem", marginTop: 4 }}>{results.election_title}</div></div></div>
            </div>
            <div className="col-6 col-md-3"><div className="kpi-card"><div style={{ minWidth: 0 }}><div className="small-caps">Total votes</div><div className="kpi-value mt-1">{results.total_votes}</div></div></div></div>
            <div className="col-6 col-md-3"><div className="kpi-card"><div style={{ minWidth: 0 }}><div className="small-caps">Status</div><div className="mt-2"><StatusBadge status={results.status} /></div></div></div></div>
            <div className="col-6 col-md-3"><div className="kpi-card"><div style={{ minWidth: 0 }}><div className="small-caps">Audit</div><div className="mt-2"><span className="badge badge-green"><ShieldCheck size={11} className="me-1" />Verified</span></div></div></div></div>
          </div>

          <div className="row g-3">
            <div className="col-12 col-lg-7">
              <div className="card">
                <div className="card-header d-flex align-items-center gap-2"><BarChart3 size={16} /> Candidate-wise results</div>
                <div className="card-body" style={{ height: 340 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barData} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#5b6b82" }} interval={0} angle={-12} textAnchor="end" height={52} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#5b6b82" }} />
                      <Tooltip cursor={{ fill: "rgba(22,58,109,0.06)" }} contentStyle={{ borderRadius: 10, border: "1px solid #dde5ee", fontSize: 13 }} />
                      <Bar dataKey="votes" name="Votes" fill="#17b877" radius={[6, 6, 0, 0]} maxBarSize={54} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
            <div className="col-12 col-lg-5">
              <div className="card">
                <div className="card-header">Vote distribution</div>
                <div className="card-body" style={{ height: 340 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" innerRadius="52%" outerRadius="78%" paddingAngle={3} stroke="none">
                        {pieData.map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #dde5ee", fontSize: 13 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="col-12">
              <div className="card">
                <div className="card-header">Official breakdown</div>
                <div className="card-body">
                  <div className="table-responsive">
                    <table className="table align-middle">
                      <thead>
                        <tr><th>Candidate</th><th className="text-end">Votes</th><th className="text-end">Share</th><th style={{ minWidth: 180 }}></th></tr>
                      </thead>
                      <tbody>
                        {results.candidates.map((c) => (
                          <tr key={c.id}>
                            <td style={{ fontWeight: 700 }}>{c.name}{c.role && <span className="text-faint ms-2" style={{ fontWeight: 500, fontSize: "0.78rem" }}>{c.role}</span>}</td>
                            <td className="text-end" style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}>{c.votes}</td>
                            <td className="text-end text-soft">{c.percentage}%</td>
                            <td>
                              <div className="result-bar"><span style={{ width: `${c.percentage}%` }} /></div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <div className="col-12">
              <div className="card" style={{ borderLeft: "4px solid var(--green-500)" }}>
                <div className="card-body d-flex gap-3">
                  <FileCheck2 size={22} style={{ color: "var(--green-600)", flexShrink: 0, marginTop: 2 }} />
                  <div>
                    <div style={{ fontWeight: 800, fontFamily: "var(--font-display)" }}>Audit verification status</div>
                    <p className="text-soft mb-0 mt-1" style={{ fontSize: "0.9rem", lineHeight: 1.65 }}>{results.audit_summary}</p>
                    {results.published_at && (
                      <div className="text-faint mt-2" style={{ fontSize: "0.78rem" }}>
                        Published {new Date(results.published_at).toLocaleString()} by the backend.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
