import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { Vote, ShieldCheck, AlertTriangle, ArrowLeft } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import CandidateCard from "../components/CandidateCard";
import { Alert, Modal, Toast, useToast } from "../components/ui";
import PageLoading from "../components/Loading";
import { listMyElections } from "../services/votingService";
import { listElectionCandidates } from "../services/electionService";
import { submitVote } from "../services/votingService";
import { getBallotSession, setBallotSession } from "../services/ballotSession";
import { friendlyMessage } from "../services/api";
import { formatDate } from "../services/electionService";

export default function Voting() {
  const { electionId } = useParams();
  const navigate = useNavigate();
  const { toast, show, dismiss } = useToast();

  const session = getBallotSession();
  const authorised = session && session.electionId === Number(electionId) && !!session.verificationToken;

  const [election, setElection] = useState(null);
  const [candidates, setCandidates] = useState(null);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [mine, cands] = await Promise.all([listMyElections(), listElectionCandidates(electionId)]);
      const e = mine.find((x) => String(x.id) === String(electionId));
      if (!e) {
        setError("This election is not available to your voter record.");
        return;
      }
      if (e.status !== "active") setError("This election is no longer accepting votes. It may have closed while you were here.");
      setElection(e);
      if (!cands.length) setError("No candidates are registered for this election. Contact the election administrator.");
      setCandidates(cands);
    } catch (err) {
      setError(friendlyMessage(err));
    }
  }, [electionId]);

  useEffect(() => {
    if (authorised) load();
  }, [authorised, load]);

  const doSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitVote(Number(electionId), {
        candidateId: selectedId,
        verificationToken: session.verificationToken,
      });
      // Keep only the receipt reference — the chosen candidate is never stored.
      setBallotSession({ ...session, referenceId: res.reference_id || null });
      show("Ballot submitted and sealed by the server.");
      navigate(`/vote/confirmed/${electionId}`, { replace: true });
    } catch (err) {
      setConfirmOpen(false);
      setError(friendlyMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  if (!authorised) {
    return (
      <DashboardLayout crumb="Voter / Ballot" title="Voting">
        <div className="card">
          <div className="card-body text-center py-5">
            <AlertTriangle size={30} className="mx-auto mb-3" style={{ color: "var(--warn-600)" }} />
            <h5 style={{ fontWeight: 700 }}>QR verification required</h5>
            <p className="text-soft mx-auto" style={{ maxWidth: "44ch", fontSize: "0.92rem" }}>
              A ballot can only be opened after the backend verifies your access token. If you reloaded this
              page, the in-memory session was dropped by design — please verify again.
            </p>
            <Link to={`/vote/qr/${electionId}`} className="btn btn-primary btn-sm">
              <ShieldCheck size={14} className="me-1" /> Go to QR verification
            </Link>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      crumb="Voter / Ballot"
      title="Cast your vote"
      actions={
        <span className="badge badge-green" style={{ fontSize: "0.74rem" }}>
          <ShieldCheck size={11} className="me-1" /> Access verified
        </span>
      }
    >
      {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
      {!election || candidates === null ? (
        <div className="card"><PageLoading label="Loading the ballot…" /></div>
      ) : (
        <div className="row g-4">
          <div className="col-12 col-lg-8">
            <div className="card mb-3">
              <div className="card-body">
                <div className="small-caps mb-1">Election</div>
                <h4 style={{ fontWeight: 700, fontSize: "1.15rem" }}>{election.title}</h4>
                {election.description && <p className="text-soft mt-2 mb-2" style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>{election.description}</p>}
                <div className="text-faint" style={{ fontSize: "0.8rem" }}>
                  Voting window: {formatDate(election.starts_at)} → {formatDate(election.ends_at)}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header d-flex align-items-center gap-2">
                <Vote size={16} /> Candidates
                <span className="badge badge-muted ms-auto" style={{ fontSize: "0.68rem" }}>Select one</span>
              </div>
              <div className="card-body d-grid gap-2">
                {candidates.map((c) => (
                  <CandidateCard
                    key={c.id}
                    candidate={c}
                    mode="ballot"
                    name="ballot-candidate"
                    selected={selectedId === c.id}
                    onSelect={(x) => setSelectedId(x.id)}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="col-12 col-lg-4">
            <div className="card" style={{ position: "sticky", top: 86 }}>
              <div className="card-body d-grid gap-3">
                <div className="d-flex align-items-center gap-2">
                  <ShieldCheck size={18} style={{ color: "var(--green-600)" }} />
                  <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>Your ballot is anonymous</span>
                </div>
                <p className="text-soft mb-0" style={{ fontSize: "0.87rem", lineHeight: 1.6 }}>
                  The candidate you select is sent directly to the server and never saved in this browser. After
                  submission you will see a reference — never a record of your choice.
                </p>
                <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  {selectedId ? (
                    <span className="d-flex align-items-center gap-2" style={{ color: "var(--green-600)" }}>
                      <ShieldCheck size={15} /> Selection ready — {candidates.find((c) => c.id === selectedId)?.name}
                    </span>
                  ) : (
                    <span className="text-faint">No candidate selected yet.</span>
                  )}
                </div>
                <button
                  className="btn btn-accent"
                  disabled={!selectedId}
                  onClick={() => setConfirmOpen(true)}
                >
                  <Vote size={16} className="me-1" /> Confirm Vote
                </button>
                <Link to="/vote" className="btn btn-ghost btn-sm">
                  <ArrowLeft size={13} className="me-1" /> Back to dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmOpen && (
        <Modal
          title="Confirm your vote"
          onClose={() => !submitting && setConfirmOpen(false)}
          footer={
            <>
              <button className="btn btn-ghost" onClick={() => setConfirmOpen(false)} disabled={submitting}>Go back</button>
              <button className="btn btn-accent" onClick={doSubmit} disabled={submitting}>
                {submitting ? <span className="spinner-ring" /> : null}
                <span className="ms-1">{submitting ? "Submitting…" : "Yes, submit my vote"}</span>
              </button>
            </>
          }
        >
          <p className="mb-2" style={{ fontWeight: 600 }}>
            Are you sure you want to submit your vote? <strong>This action cannot be undone.</strong>
          </p>
          <Alert variant="info" className="mb-0">
            <span style={{ fontSize: "0.85rem" }}>
              The server will re-check your eligibility and duplicate-vote rules before sealing the ballot. You
              will not be shown which candidate you selected afterwards.
            </span>
          </Alert>
        </Modal>
      )}

      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
