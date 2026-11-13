import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { QrCode, ScanLine, Keyboard, ArrowLeft, CheckCircle2, XCircle, ShieldAlert, Camera, CameraOff } from "lucide-react";
import DashboardLayout from "../components/DashboardLayout";
import { Alert, Toast, useToast } from "../components/ui";
import PageLoading from "../components/Loading";
import { listMyElections } from "../services/votingService";
import { verifyQr } from "../services/qrService";
import { friendlyMessage, DEMO_MODE } from "../services/api";
import { setBallotSession, clearBallotSession } from "../services/ballotSession";

export default function QRVerification() {
  const { electionId } = useParams();
  const navigate = useNavigate();
  const { toast, show, dismiss } = useToast();

  const [election, setElection] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null); // { valid, reason, message }
  const [error, setError] = useState(null);

  // camera
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const scannerRef = useRef(null);
  const regionRef = useRef(null);
  const scanningRef = useRef(false);

  const stopCamera = useCallback(async () => {
    try {
      if (scannerRef.current) {
        await scannerRef.current.stop();
        scannerRef.current.clear?.();
      }
    } catch { /* already stopped */ }
    scannerRef.current = null;
    setCameraOn(false);
  }, []);

  const loadElection = useCallback(async () => {
    try {
      const mine = await listMyElections();
      const e = mine.find((x) => String(x.id) === String(electionId));
      if (!e) setLoadError("This election is not available to your voter record. If you believe this is wrong, contact the election administrator.");
      else setElection(e);
    } catch (err) {
      setLoadError(friendlyMessage(err));
    }
  }, [electionId]);

  useEffect(() => {
    loadElection();
    return () => { stopCamera(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submitToken = useCallback(
    async (raw) => {
      const value = (raw ?? token).trim();
      if (!value || busy) return;
      setBusy(true);
      setError(null);
      setResult(null);
      try {
        const res = await verifyQr(value, electionId);
        if (res.valid) {
          // Server confirmed: token valid, voter eligible, no prior ballot.
          setBallotSession({
            electionId: Number(electionId),
            verificationToken: res.verification_token,
            voterId: res.voter_id || null,
            referenceId: null,
          });
          await stopCamera();
          show("Access verified by the backend.");
          navigate(`/vote/election/${electionId}`, { replace: true });
        } else {
          setResult({ valid: false, reason: res.reason, message: res.message });
          setToken("");
        }
      } catch (err) {
        setError(friendlyMessage(err));
      } finally {
        setBusy(false);
      }
    },
    [token, busy, electionId, navigate, show, stopCamera]
  );

  const startCamera = async () => {
    setCameraError(null);
    setError(null);
    try {
      const { Html5Qrcode } = await import("html5-qrcode");
      setCameraOn(true);
      // wait for the scan region element to be mounted
      await new Promise((r) => setTimeout(r, 80));
      if (!regionRef.current) {
        setCameraOn(false);
        setCameraError("Camera scanning is unavailable on this device or browser (permissions / no camera). You can still enter the token manually below.");
        return;
      }
      const scanner = new Html5Qrcode("qr-scan-region", { verbose: false });
      scannerRef.current = scanner;
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 220, height: 220 } },
        (decoded) => {
          if (scanningRef.current) return;
          scanningRef.current = true;
          stopCamera();
          submitToken(decoded);
        },
        () => { /* per-frame decode misses — ignore */ }
      );
    } catch (err) {
      setCameraOn(false);
      scannerRef.current = null;
      setCameraError("Camera scanning is unavailable on this device or browser (permissions / no camera). You can still enter the token manually below.");
    }
  };

  if (loadError) {
    return (
      <DashboardLayout crumb="Voter / Access" title="QR Verification">
        <Alert variant="danger" className="mb-3">{loadError}</Alert>
        <Link to="/vote" className="btn btn-ghost btn-sm"><ArrowLeft size={14} className="me-1" /> Back to my elections</Link>
      </DashboardLayout>
    );
  }
  if (!election) return <DashboardLayout crumb="Voter / Access" title="QR Verification"><PageLoading label="Loading election…" /></DashboardLayout>;

  return (
    <DashboardLayout crumb="Voter / Access" title="QR Verification">
      <div className="row g-4">
        <div className="col-12 col-lg-7">
          <div className="card">
            <div className="card-header d-flex align-items-center gap-2"><ScanLine size={16} /> Step 1 — verify access</div>
            <div className="card-body">
              <div className="d-flex align-items-center gap-2 mb-3">
                <span className="badge badge-navy">{election.title}</span>
              </div>
              <p className="text-soft" style={{ fontSize: "0.9rem", lineHeight: 1.6 }}>
                Present the QR access token issued by the election administrator. The backend checks the token's
                signature, expiry and single-use status, then confirms your eligibility. A QR code alone is never
                treated as proof of identity.
              </p>

              {cameraError && <Alert variant="warning" className="mb-3">{cameraError}</Alert>}
              {error && <Alert variant="danger" className="mb-3">{error}</Alert>}

              {result && !result.valid && (
                <Alert variant="danger" className="mb-3">
                  <div className="d-flex gap-2 align-items-start">
                    <XCircle size={17} className="flex-shrink-0 mt-1" />
                    <div>
                      <div className="fw-bold mb-1">
                        Verification failed — {String(result.reason || "invalid").replaceAll("_", " ")}
                      </div>
                      {result.message}
                    </div>
                  </div>
                </Alert>
              )}
              {result && result.valid && <Alert variant="success">Access verified — opening the ballot…</Alert>}

              {/* camera */}
              <div className="border rounded p-3 mb-4" style={{ borderRadius: "var(--radius-md)", borderColor: "var(--line)" }}>
                <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div className="d-flex align-items-center gap-2">
                    {cameraOn ? <CameraOff size={17} /> : <Camera size={17} />}
                    <span style={{ fontWeight: 700, fontSize: "0.92rem" }}>{cameraOn ? "Scanning…" : "Scan with camera"}</span>
                  </div>
                  {cameraOn ? (
                    <button className="btn btn-ghost btn-sm" onClick={stopCamera}>Stop camera</button>
                  ) : (
                    <button className="btn btn-ghost btn-sm" onClick={startCamera} disabled={busy}>Start camera</button>
                  )}
                </div>
                {cameraOn && (
                  <div id="qr-scan-region" ref={regionRef} className="mt-3" style={{ maxWidth: 320, margin: "0.75rem auto 0", borderRadius: "var(--radius-md)", overflow: "hidden", background: "#000" }} />
                )}
                {!cameraOn && (
                  <div className="text-faint mt-2" style={{ fontSize: "0.8rem" }}>
                    Works when the device has a camera and you allow access. If it's unavailable, use manual entry.
                  </div>
                )}
              </div>

              <hr className="divider mb-4" />

              {/* manual entry */}
              <div className="d-flex align-items-center gap-2 mb-2">
                <Keyboard size={16} className="text-faint" />
                <span style={{ fontWeight: 700, fontSize: "0.92rem" }}>Enter token manually</span>
              </div>
              <form
                onSubmit={(e) => { e.preventDefault(); submitToken(); }}
                className="d-flex gap-2 flex-wrap"
              >
                <input
                  className="form-control"
                  style={{ fontFamily: "var(--font-display)", fontWeight: 700, letterSpacing: "0.04em", flex: "1 1 260px", textTransform: "uppercase" }}
                  placeholder="e.g. EVQR-DEMO-XXXX-XXXX"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  disabled={busy}
                  aria-label="Access token"
                />
                <button type="submit" className="btn btn-primary" disabled={busy || !token.trim()}>
                  {busy ? <span className="spinner-ring" /> : <ShieldAlert size={15} className="me-1" />}
                  <span className="ms-1">{busy ? "Verifying…" : "Verify token"}</span>
                </button>
              </form>

              {DEMO_MODE && (
                <div className="demo-hint mt-3">
                  <strong>Demo test tokens:</strong>{" "}
                  <code>DEMO-VALID-TOKEN</code> (success) · <code>DEMO-EXPIRED-TOKEN</code> (expired) · <code>DEMO-USED-TOKEN</code> (already used)
                  <div className="mt-1">A real deployment issues tokens only through the admin QR page — the backend signs and expires them.</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-5">
          <div className="card">
            <div className="card-header d-flex align-items-center gap-2"><QrCode size={16} /> How verification works</div>
            <div className="card-body d-grid gap-3" style={{ fontSize: "0.88rem" }}>
              {[
                ["Token checked server-side", "Signature, expiry and single-use state are validated by the backend — never in the browser."],
                ["Eligibility re-checked", "Your voter record must be eligible for this election, and you must not have voted already."],
                ["Ballot session", "On success a short-lived session token (kept in memory only) opens the ballot. Reload the page and you must verify again."],
              ].map(([t, d]) => (
                <div className="d-flex gap-3" key={t}>
                  <CheckCircle2 size={18} className="flex-shrink-0 mt-05" style={{ marginTop: 2, color: "var(--green-600)" }} />
                  <div>
                    <div style={{ fontWeight: 700 }}>{t}</div>
                    <div className="text-soft">{d}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <Toast toast={toast} onDismiss={dismiss} />
    </DashboardLayout>
  );
}
