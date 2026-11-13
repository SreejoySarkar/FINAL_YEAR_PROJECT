import { useEffect, useState, useCallback } from "react";
import { Plus, Eye, Pencil, Trash2, Vote, RefreshCw } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { PageHeader, StatusBadge, Modal, ConfirmModal, Alert, Toast, useToast, EmptyState } from "../components/ui";
import PageLoading from "../components/Loading";
import { listElections, createElection, updateElection, deleteElection, getElection, publishElection, closeElection, toLocalInput, toIso, formatDate } from "../services/electionService";
import { friendlyMessage } from "../services/api";

const EMPTY_FORM = { title: "", description: "", starts_at: "", ends_at: "", status: "draft" };

export default function ElectionManagement() {
  const [elections, setElections] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null); // election being edited or null for new
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);

  const [viewing, setViewing] = useState(null); // election detail object
  const [deleting, setDeleting] = useState(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const { toast, show, dismiss } = useToast();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setElections(await listElections());
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, status: "draft" });
    setFormError(null);
    setFormOpen(true);
  };

  const openEdit = (e) => {
    setEditing(e);
    setForm({
      title: e.title,
      description: e.description || "",
      starts_at: toLocalInput(e.starts_at),
      ends_at: toLocalInput(e.ends_at),
      status: e.status,
    });
    setFormError(null);
    setFormOpen(true);
  };

  const save = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (!form.title.trim()) return setFormError("Election title is required.");
    if (!form.starts_at || !form.ends_at) return setFormError("Please set both start and end dates.");
    if (new Date(form.ends_at) <= new Date(form.starts_at)) return setFormError("The end date must be after the start date.");
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        starts_at: toIso(form.starts_at),
        ends_at: toIso(form.ends_at),
      };
      if (editing) {
        await updateElection(editing.id, payload);
        show("Election updated.");
      } else {
        await createElection(payload);
        show("Election created.");
      }
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(friendlyMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    setDeleteBusy(true);
    try {
      await deleteElection(deleting.id);
      show("Election deleted.");
      setDeleting(null);
      await load();
    } catch (err) {
      show(friendlyMessage(err), "error");
    } finally {
      setDeleteBusy(false);
    }
  };

  const changeElectionState = async (election, action) => {
    try {
      if (action === "publish") await publishElection(election.id);
      else await closeElection(election.id);
      show(action === "publish" ? "Election published." : "Election closed.");
      await load();
    } catch (err) {
      show(friendlyMessage(err), "error");
    }
  };

  const openView = async (e) => {
    try {
      setViewing(await getElection(e.id));
    } catch (err) {
      show(friendlyMessage(err), "error");
    }
  };

  return (
    <DashboardLayout
      crumb="Admin / Elections"
      title="Election Management"
      actions={
        <>
          <button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={14} className="me-1" /> Refresh</button>
          <button className="btn btn-primary btn-sm" onClick={openCreate}><Plus size={14} className="me-1" /> New election</button>
        </>
      }
    >
      <PageHeader title="All elections" subtitle="Create elections, set their voting window and status. Only elections the backend marks as active accept ballots.">
        <span className="badge badge-navy">{elections?.length ?? "…"} elections</span>
      </PageHeader>

      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {loading ? (
        <div className="card"><PageLoading label="Loading elections…" /></div>
      ) : (
        <div className="card">
          <div className="table-responsive">
            <table className="table align-middle">
              <thead>
                <tr>
                  <th>Election</th>
                  <th>Status</th>
                  <th>Starts</th>
                  <th>Ends</th>
                  <th className="text-center">Candidates</th>
                  <th className="text-center">Ballots</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {elections?.length === 0 && (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState icon={Vote} title="No elections yet" text="Create your first election to start managing candidates and voters.">
                        <button className="btn btn-primary btn-sm" onClick={openCreate}><Plus size={14} className="me-1" /> New election</button>
                      </EmptyState>
                    </td>
                  </tr>
                )}
                {elections?.map((e) => (
                  <tr key={e.id}>
                    <td>
                      <div style={{ fontWeight: 700 }}>{e.title}</div>
                      <div className="text-faint" style={{ fontSize: "0.78rem" }}>#{e.id}</div>
                    </td>
                    <td><StatusBadge status={e.status} /></td>
                    <td className="text-soft" style={{ whiteSpace: "nowrap" }}>{formatDate(e.starts_at)}</td>
                    <td className="text-soft" style={{ whiteSpace: "nowrap" }}>{formatDate(e.ends_at)}</td>
                    <td className="text-center">{e.candidates_count ?? "—"}</td>
                    <td className="text-center">{typeof e.votes_cast === "number" ? e.votes_cast : "—"}</td>
                    <td>
                      <div className="d-flex gap-1 justify-content-end">
                        <button className="btn btn-ghost btn-sm" style={{ padding: "0.3rem 0.5rem" }} title="View" onClick={() => openView(e)}><Eye size={14} /></button>
                        {e.status === "draft" && <>
                          <button className="btn btn-success btn-sm" title="Publish (requires candidates, eligibility and QR tokens)" onClick={() => changeElectionState(e, "publish")}>Publish</button>
                          <button className="btn btn-ghost btn-sm" style={{ padding: "0.3rem 0.5rem" }} title="Edit draft" onClick={() => openEdit(e)}><Pencil size={14} /></button>
                          <button className="btn btn-danger-soft btn-sm" style={{ padding: "0.3rem 0.5rem" }} title="Delete draft" onClick={() => setDeleting(e)}><Trash2 size={14} /></button>
                        </>}
                        {e.status === "active" && <button className="btn btn-warning btn-sm" title="Close election" onClick={() => changeElectionState(e, "close")}>Close</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* create / edit modal */}
      {formOpen && (
        <Modal
          title={editing ? `Edit election — ${editing.title}` : "Create a new election"}
          onClose={() => !saving && setFormOpen(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setFormOpen(false)} disabled={saving}>Cancel</button>
              <button className="btn btn-primary" onClick={save} disabled={saving}>
                {saving ? <span className="spinner-ring" /> : null}
                <span className="ms-1">{saving ? "Saving…" : editing ? "Save changes" : "Create election"}</span>
              </button>
            </>
          }
        >
          <form onSubmit={save} noValidate>
            {formError && <Alert variant="danger" className="mb-3">{formError}</Alert>}
            <div className="mb-3">
              <label className="form-label" htmlFor="el-title">Election title</label>
              <input id="el-title" className="form-control" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Board of Directors Election 2026" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="el-desc">Description</label>
              <textarea id="el-desc" className="form-control" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What is being voted on and who is eligible?" />
            </div>
            <div className="row g-3 mb-3">
              <div className="col-sm-6">
                <label className="form-label" htmlFor="el-start">Start date & time</label>
                <input id="el-start" type="datetime-local" className="form-control" value={form.starts_at} onChange={(e) => setForm({ ...form, starts_at: e.target.value })} />
              </div>
              <div className="col-sm-6">
                <label className="form-label" htmlFor="el-end">End date & time</label>
                <input id="el-end" type="datetime-local" className="form-control" value={form.ends_at} onChange={(e) => setForm({ ...form, ends_at: e.target.value })} />
              </div>
            </div>
            <div className="alert alert-info mb-1" style={{ fontSize: "0.82rem" }}>
              New elections are created as drafts. Publish them after adding at least two candidates, assigning eligible voters, and generating their QR tokens.
            </div>
          </form>
        </Modal>
      )}

      {/* detail modal */}
      {viewing && (
        <Modal title={viewing.title} onClose={() => setViewing(null)}>
          <div className="mb-3"><StatusBadge status={viewing.status} /> {viewing.results_verified && viewing.results_published && <span className="badge badge-green ms-1">Results verified</span>}</div>
          <p className="text-soft" style={{ fontSize: "0.92rem", lineHeight: 1.65 }}>{viewing.description || "No description provided."}</p>
          <div className="row g-3" style={{ fontSize: "0.9rem" }}>
            <div className="col-6">
              <div className="small-caps">Opens</div>
              <div className="fw-semibold mt-1">{formatDate(viewing.starts_at)}</div>
            </div>
            <div className="col-6">
              <div className="small-caps">Closes</div>
              <div className="fw-semibold mt-1">{formatDate(viewing.ends_at)}</div>
            </div>
            <div className="col-6">
              <div className="small-caps">Ballots cast</div>
              <div className="fw-semibold mt-1">{typeof viewing.votes_cast === "number" ? viewing.votes_cast : "—"}</div>
            </div>
          </div>
          <hr className="divider my-3" />
          <div className="small-caps mb-2">Candidates ({viewing.candidates?.length ?? 0})</div>
          {viewing.candidates?.length ? (
            <ul className="list-unstyled d-grid gap-2 mb-0">
              {viewing.candidates.map((c) => (
                <li key={c.id} className="d-flex align-items-center gap-2" style={{ fontSize: "0.9rem" }}>
                  <span className="badge badge-navy" style={{ minWidth: 26, justifyContent: "center" }}>{c.id}</span>
                  <span style={{ fontWeight: 600 }}>{c.name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-faint mb-0" style={{ fontSize: "0.86rem" }}>No candidates added yet.</p>
          )}
        </Modal>
      )}

      {deleting && (
        <ConfirmModal
          title="Delete election"
          message={`“${deleting.title}” will be permanently removed, including its QR tokens and ballot record. This cannot be undone. Continue?`}
          confirmLabel="Delete election"
          variant="primary"
          busy={deleteBusy}
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
        />
      )}

      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
