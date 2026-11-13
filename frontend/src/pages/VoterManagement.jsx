import { useEffect, useState, useCallback } from "react";
import { Search, Users, Eye, Plus, RefreshCw, ShieldQuestion } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, Modal, Alert, Toast, useToast, EmptyState, StatusBadge } from "../components/ui";
import PageLoading from "../components/Loading";
import { listVoters, createVoter } from "../services/voterService";
import { friendlyMessage } from "../services/api";
import { formatDate } from "../services/electionService";

export default function VoterManagement() {
  const [voters, setVoters] = useState(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);

  const [viewing, setViewing] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ name: "", voter_id: "", email: "", department: "", is_eligible: true });
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const { toast, show, dismiss } = useToast();

  const load = useCallback(async (q = "") => {
    setError(null);
    try {
      setVoters(await listVoters(q.trim() || undefined));
    } catch (err) {
      setError(friendlyMessage(err));
    }
  }, []);

  useEffect(() => {
    setVoters(null);
    load(search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const submitAdd = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (!form.name.trim() || !form.voter_id.trim()) return setFormError("Voter ID and full name are required.");
    setSaving(true);
    try {
      await createVoter(form);
      show("Voter registered.");
      setAddOpen(false);
      setForm({ name: "", voter_id: "", email: "", department: "", is_eligible: true });
      await load(search);
    } catch (err) {
      setFormError(friendlyMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout
      crumb="Admin / Voters"
      title="Voter Management"
      actions={
        <>
          <button className="btn btn-ghost btn-sm" onClick={() => load(search)}><RefreshCw size={14} className="me-1" /> Refresh</button>
          <button className="btn btn-primary btn-sm" onClick={() => { setFormError(null); setAddOpen(true); }}><Plus size={14} className="me-1" /> Register voter</button>
        </>
      }
    >
      <PageHeader title="Registered voter records" subtitle="Manage registered voter records. Election-specific eligibility is assigned from QR management; the selected candidate is never exposed in voter records.">
        <div className="search-box" style={{ minWidth: 260 }}>
          <Search size={16} className="search-icon" />
          <input
            className="form-control"
            placeholder="Search name, voter ID, email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search voters"
          />
        </div>
      </PageHeader>

      <Alert variant="info" className="mb-3 d-flex align-items-start gap-2">
        <span className="d-flex gap-2">
          <ShieldQuestion size={16} className="flex-shrink-0 mt-1" />
          <span style={{ fontSize: "0.86rem" }}>
            Private data is kept to a minimum: no ballot contents, IP history or session details are displayed. Eligibility and voting status are shown exactly as the backend reports them.
          </span>
        </span>
      </Alert>

      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {voters === null ? (
        <div className="card"><PageLoading label="Loading voters…" /></div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table align-middle">
              <thead>
                <tr>
                  <th>Voter ID</th>
                  <th>Name</th>
                  <th>Department</th>
                  <th>Account status</th>
                  <th>Voting status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {voters.length === 0 && (
                  <tr>
                    <td colSpan={6}>
                      <EmptyState icon={Users} title="No voters match" text={search ? `No results for “${search}”. Try a different search.` : "Register the first voter to begin."} />
                    </td>
                  </tr>
                )}
                {voters.map((v) => (
                  <tr key={v.voter_id || v.id}>
                    <td><code className="inline">{v.voter_id}</code></td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{v.name}</div>
                      <div className="text-faint" style={{ fontSize: "0.78rem" }}>{v.email || "—"}</div>
                    </td>
                    <td className="text-soft">{v.department || "—"}</td>
                    <td>
                      {v.is_eligible ? <span className="badge badge-green">Active</span> : <span className="badge badge-red">Inactive</span>}
                    </td>
                    <td>
                      <span className={`badge ${v.has_voted_elections?.length ? "badge-green" : "badge-muted"}`}>{v.voting_status || "Not reported"}</span>
                    </td>
                    <td>
                      <div className="d-flex justify-content-end">
                        <button className="btn btn-ghost btn-sm" style={{ padding: "0.3rem 0.5rem" }} title="View" onClick={() => setViewing(v)}><Eye size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {viewing && (
        <Modal title={`Voter record — ${viewing.voter_id}`} onClose={() => setViewing(null)}>
          <div className="row g-3" style={{ fontSize: "0.92rem" }}>
            <div className="col-6"><div className="small-caps">Name</div><div className="fw-semibold mt-1">{viewing.name}</div></div>
            <div className="col-6"><div className="small-caps">Email</div><div className="fw-semibold mt-1">{viewing.email || "—"}</div></div>
            <div className="col-6"><div className="small-caps">Department</div><div className="fw-semibold mt-1">{viewing.department || "—"}</div></div>
            <div className="col-6"><div className="small-caps">Account status</div><div className="mt-1">{viewing.is_eligible ? <span className="badge badge-green">Active</span> : <span className="badge badge-red">Inactive</span>}</div></div>
          </div>
          <hr className="divider my-3" />
          <div className="small-caps mb-2">Voting status</div>
          {viewing.has_voted_elections?.length ? (
            <ul className="mb-0" style={{ fontSize: "0.88rem" }}>{viewing.has_voted_elections.map((title) => <li key={title}>{title}</li>)}</ul>
          ) : (
            <p className="text-faint mb-0" style={{ fontSize: "0.88rem" }}>{viewing.voting_status || "No voting status was returned by the backend."}</p>
          )}
          <Alert variant="warning" className="mt-3 mb-0">
            <span style={{ fontSize: "0.82rem" }}>By design, the candidate a voter selected is never stored in a viewable form and cannot be displayed here.</span>
          </Alert>
        </Modal>
      )}

      {addOpen && (
        <Modal
          title="Register a voter"
          onClose={() => !saving && setAddOpen(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setAddOpen(false)} disabled={saving}>Cancel</button>
              <button className="btn btn-primary" onClick={submitAdd} disabled={saving}>
                {saving ? <span className="spinner-ring" /> : null}
                <span className="ms-1">{saving ? "Registering…" : "Register voter"}</span>
              </button>
            </>
          }
        >
          <form onSubmit={submitAdd} noValidate>
            {formError && <Alert variant="danger" className="mb-3">{formError}</Alert>}
            <div className="row g-3 mb-3">
              <div className="col-sm-6">
                <label className="form-label" htmlFor="v-name">Full name</label>
                <input id="v-name" className="form-control" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="col-sm-6">
                <label className="form-label" htmlFor="v-id">Voter ID</label>
                <input id="v-id" className="form-control" value={form.voter_id} onChange={(e) => setForm({ ...form, voter_id: e.target.value })} placeholder="EV-1009" />
              </div>
            </div>
            <div className="row g-3 mb-3">
              <div className="col-sm-6">
                <label className="form-label" htmlFor="v-email">Email</label>
                <input id="v-email" type="email" className="form-control" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </div>
              <div className="col-sm-6">
                <label className="form-label" htmlFor="v-dept">Department</label>
                <input id="v-dept" className="form-control" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
              </div>
            </div>
            <div className="form-check form-switch">
              <input
                id="v-elig"
                type="checkbox"
                className="form-check-input"
                checked={form.is_eligible}
                onChange={(e) => setForm({ ...form, is_eligible: e.target.checked })}
              />
              <label className="form-check-label" htmlFor="v-elig" style={{ fontWeight: 600, fontSize: "0.9rem" }}>Mark voter record as active</label>
            </div>
          </form>
        </Modal>
      )}

      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
