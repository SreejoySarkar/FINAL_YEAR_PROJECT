import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, ReceiptText, Lock } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { Alert } from "../components/ui";
import PageLoading from "../components/Loading";
import { listMyElections } from "../services/votingService";
import { getBallotSession, clearBallotSession } from "../services/ballotSession";
import { friendlyMessage } from "../services/api";

export default function VoteConfirmation() {
  const { electionId } = useParams();
  const navigate = useNavigate();
  const [election, setElection] = useState(null);
  const [error, setError] = useState(null);
  const session = getBallotSession();
  const reference = session && session.electionId === Number(electionId) ? session.referenceId : null;

  useEffect(() => {
    (async () => {
      try {
        const mine = await listMyElections();
        setElection(mine.find((x) => String(x.id) === String(electionId)) || null);
      } catch (err) {
        setError(friendlyMessage(err));
      }
    })();
  }, [electionId]);

  const goHome = () => {
    clearBallotSession();
    navigate("/vote", { replace: true });
  };

  return (
    <DashboardLayout crumb="Voter / Confirmation" title="Vote confirmation">
      <div className="row justify-content-center">
        <div className="col-12 col-md-8 col-lg-6">
          <div className="card text-center">
            <div className="card-body py-5">
              <div
                style={{
                  width: 74, height: 74, borderRadius: 20, margin: "0 auto 1.2rem",
                  background: "var(--green-100)", color: "var(--green-600)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >
                <CheckCircle2 size={38} />
              </div>
              <h3 style={{ fontWeight: 700 }}>Your vote has been successfully submitted!</h3>
              <p className="text-soft" style={{ fontSize: "0.95rem", maxWidth: "44ch", margin: "0.6rem auto 1.4rem" }}>
                The ballot was validated and sealed by the server. No further action is needed — and the system
                will never show you which candidate you selected.
              </p>

              {error && <Alert variant="danger" className="mb-3 text-start">{error}</Alert>}
              {!election && !error && <PageLoading label="Loading election details…" />}

              {election && (
                <div className="card mb-3 text-start" style={{ background: "#fafcfe" }}>
                  <div className="card-body" style={{ padding: "1rem 1.2rem" }}>
                    <div className="row g-3">
                      <div className="col-8">
                        <div className="small-caps">Election</div>
                        <div className="fw-bold mt-1" style={{ fontSize: "0.95rem" }}>{election.title}</div>
                      </div>
                      <div className="col-4">
                        <div className="small-caps">Status</div>
                        <div className="mt-1"><span className="badge badge-green">Ballot recorded</span></div>
                      </div>
                      <div className="col-12">
                        <div className="small-caps">Ballot reference</div>
                        <div className="fw-bold mt-1 d-flex align-items-center gap-2" style={{ fontSize: "0.95rem", fontFamily: "var(--font-display)", letterSpacing: "0.03em" }}>
                          <ReceiptText size={15} className="text-faint" />
                          {reference || "Issued by the server (see receipt e-mail, if provided)"}
                        </div>
                        {!reference && (
                          <div className="text-faint mt-1" style={{ fontSize: "0.78rem" }}>
                            The reference was delivered during submission; it is intentionally not persisted in this browser.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="d-flex align-items-center justify-content-center gap-2 mb-3" style={{ fontSize: "0.8rem", color: "var(--ink-faint)", fontWeight: 600 }}>
                <Lock size={13} /> Ballot contents are sealed and anonymous by design.
              </div>

              <button className="btn btn-primary" onClick={goHome}>
                Return to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
