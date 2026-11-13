import { useEffect, useState, useCallback } from "react";
import { Plus, Users, RefreshCw } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import CandidateCard from "../components/CandidateCard";
import { PageHeader, Modal, ConfirmModal, Alert, Toast, useToast, EmptyState } from "../components/ui";
import PageLoading from "../components/Loading";
import { listCandidates, createCandidate, updateCandidate, deleteCandidate } from "../services/candidateService";
import { listElections } from "../services/electionService";
import { friendlyMessage } from "../services/api";

const EMPTY_FORM = { name: "", description: "", election_id: "" };

export default function CandidateManagement() {
  const [candidates, setCandidates] = useState(null);
  const [elections, setElections] = useState([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  const { toast, show, dismiss } = useToast();

  const load = useCallback(async (electionFilter) => {
    setError(null);
    try {
      const [cands, els] = await Promise.all([
        listCandidates(electionFilter === "all" ? null : electionFilter),
        listElections(),
      ]);
      setCandidates(cands);
      setElections(els);
    } catch (err) {
      setError(friendlyMessage(err));
    }
  }, []);

  useEffect(() => {
    setCandidates(null);
    load(filter);
  }, [filter, load]);

  const electionTitle = (id) => elections.find((e) => e.id === Number(id))?.title || `Election #${id}`;

  const openCreate = () => {
    setEditing(null);
    setForm({ ...EMPTY_FORM, election_id: filter !== "all" ? String(filter) : "" });
    setFormError(null);
    setFormOpen(true);
  };

  const openEdit = (c) => {
    setEditing(c);
    setForm({ name: c.name, description: c.description || "", election_id: String(c.election_id) });
    setFormError(null);
    setFormOpen(true);
  };

  const save = async (e) => {
    e?.preventDefault();
    setFormError(null);
    if (!form.name.trim()) return setFormError("Candidate name is required.");
    if (!form.election_id) return setFormError("Please choose the election this candidate belongs to.");
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        election_id: Number(form.election_id),
      };
      if (editing) {
        await updateCandidate(editing.id, payload);
        show("Candidate updated.");
      } else {
        await createCandidate(payload);
        show("Candidate added.");
      }
      setFormOpen(false);
      await load(filter);
    } catch (err) {
      setFormError(friendlyMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    setDeleteBusy(true);
    try {
      await deleteCandidate(deleting.id);
      show("Candidate removed.");
      setDeleting(null);
      await load(filter);
    } catch (err) {
      show(friendlyMessage(err), "error");
    } finally {
      setDeleteBusy(false);
    }
  };

  return (
    <DashboardLayout
      crumb="Admin / Candidates"
      title="Candidate Management"
      actions={
        <>
          <button className="btn btn-ghost btn-sm" onClick={() => load(filter)}><RefreshCw size={14} className="me-1" /> Refresh</button>
          <button className="btn btn-primary btn-sm" onClick={openCreate}><Plus size={14} className="me-1" /> Add candidate</button>
        </>
      }
    >
      <PageHeader title="Candidates" subtitle="Add candidates and associate them with draft elections. The current backend stores names and descriptions only.">
        <select className="form-select form-select-sm" style={{ width: "auto", minWidth: 220 }} value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by election">
          <option value="all">All elections</option>
          {elections.map((e) => (
            <option key={e.id} value={e.id}>{e.title}</option>
          ))}
        </select>
      </PageHeader>

      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {candidates === null ? (
        <div className="card"><PageLoading label="Loading candidates…" /></div>
      ) : candidates.length === 0 ? (
        <div className="card">
          <EmptyState icon={Users} title="No candidates found" text="Add the first candidate for the selected election.">
            <button className="btn btn-primary btn-sm" onClick={openCreate}><Plus size={14} className="me-1" /> Add candidate</button>
          </EmptyState>
        </div>
      ) : (
        <div className="row g-3">
          {candidates.map((c) => (
            <div className="col-12 col-md-6 col-xl-4" key={c.id}>
              <CandidateCard candidate={c} electionLabel={electionTitle(c.election_id)} onEdit={openEdit} onDelete={setDeleting} />
            </div>
          ))}
        </div>
      )}

      {formOpen && (
        <Modal
          title={editing ? `Edit candidate — ${editing.name}` : "Add a candidate"}
          onClose={() => !saving && setFormOpen(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setFormOpen(false)} disabled={saving}>Cancel</button>
              <button className="btn btn-primary" onClick={save} disabled={saving}>
                {saving ? <span className="spinner-ring" /> : null}
                <span className="ms-1">{saving ? "Saving…" : editing ? "Save changes" : "Add candidate"}</span>
              </button>
            </>
          }
        >
          <form onSubmit={save} noValidate>
            {formError && <Alert variant="danger" className="mb-3">{formError}</Alert>}
            <div className="mb-3">
              <label className="form-label" htmlFor="cand-name">Candidate name</label>
              <input id="cand-name" className="form-control" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Full name" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="cand-desc">Description</label>
              <textarea id="cand-desc" className="form-control" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Short biography or platform statement shown on the ballot." />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="cand-election">Election</label>
              <select id="cand-election" className="form-select" value={form.election_id} onChange={(e) => setForm({ ...form, election_id: e.target.value })}>
                <option value="">Select an election…</option>
                {elections.map((e) => (
                  <option key={e.id} value={e.id}>{e.title}</option>
                ))}
              </select>
            </div>
          </form>
        </Modal>
      )}

      {deleting && (
        <ConfirmModal
          title="Remove candidate"
          message={`“${deleting.name}” will be removed from ${electionTitle(deleting.election_id)}. Existing sealed ballots are unaffected. Continue?`}
          confirmLabel="Remove candidate"
          busy={deleteBusy}
          onConfirm={confirmDelete}
          onCancel={() => setDeleting(null)}
        />
      )}

      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
