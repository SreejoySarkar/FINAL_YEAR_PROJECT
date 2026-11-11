import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, Eye, EyeOff, KeyRound, ArrowLeft, Server } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { login as loginRequest, verifyOtp } from "../services/authService";
import { friendlyMessage } from "../services/api";
import { DEMO_MODE } from "../services/api";
import { DEMO_CREDENTIALS } from "../services/mockBackend";
import { Alert } from "../components/ui";
import { BrandMark } from "../components/Navbar";

const SECURITY_POINTS = [
  ["Secure authentication", "Role-based sessions with optional one-time codes, enforced by the backend."],
  ["Anonymous ballots", "Your voter ID is never linked to the candidate you choose."],
  ["One ballot per voter", "Duplicate votes are detected and rejected server-side."],
  ["Audit-verified results", "Counts are published only after the audit trail verifies the seal."],
];

export default function Login() {
  const { user, role, completeLogin, initializing, sessionNotice, clearSessionNotice } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const expiredNotice = location.state?.notice || sessionNotice;

  const [accountType, setAccountType] = useState("admin");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  // OTP step (only shown when the backend requests a second factor)
  const [otpStage, setOtpStage] = useState(false);
  const [otpSession, setOtpSession] = useState(null);
  const [otpCode, setOtpCode] = useState("");
  const [otpMessage, setOtpMessage] = useState(null);

  useEffect(() => {
    if (!initializing && user) {
      // Already signed in — go straight to the right area.
      navigate(role === "admin" ? "/admin" : "/vote", { replace: true });
    }
  }, [initializing, user, role, navigate]);
  if (!initializing && user) return null;

  const redirectFor = (u) => navigate(u?.role === "admin" ? "/admin" : "/vote", { replace: true });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    if (!identifier.trim() || !password) {
      setError("Please enter your email / voter ID and password.");
      return;
    }
    setBusy(true);
    try {
      const res = await loginRequest(identifier.trim(), password, accountType);
      if (res.otpRequired) {
        setOtpStage(true);
        setOtpSession(res.otpSession);
        setOtpMessage(res.message || "A one-time code was sent to you.");
        setOtpCode("");
      } else {
        completeLogin(res);
        redirectFor(res.user);
      }
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const handleOtp = async (e) => {
    e.preventDefault();
    setError(null);
    if (!otpCode.trim()) {
      setError("Please enter the one-time code.");
      return;
    }
    setBusy(true);
    try {
      const res = await verifyOtp(otpCode.trim(), otpSession);
      completeLogin(res);
      redirectFor(res.user);
    } catch (err) {
      setError(friendlyMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="auth-side">
        <div className="hero-grid" aria-hidden="true" />
        <div style={{ position: "relative" }}>
          <Link to="/" className="d-flex align-items-center gap-2 text-white mb-5" style={{ textDecoration: "none" }}>
            <BrandMark />
            <span className="brand-name">Secure E-Voting System</span>
          </Link>
          <h2 style={{ color: "#fff", fontSize: "clamp(1.5rem, 2.6vw, 2.1rem)", maxWidth: "24ch", lineHeight: 1.25 }}>
            Sign in to the <span className="text-green-accent">secured voting area</span>
          </h2>
          <ul className="auth-list mt-5">
            {SECURITY_POINTS.map(([t, d]) => (
              <li key={t}>
                <span className="tick"><ShieldCheck size={17} /></span>
                <span>
                  <span className="t d-block">{t}</span>
                  <span className="d">{d}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div style={{ position: "relative", fontSize: "0.78rem", color: "#7d92b0" }}>
          Access is role-based and re-verified on every request by the Django backend.
        </div>
      </div>

      <div className="auth-form-col">
        <div className="auth-card">
          <div className="mb-3">
            <button className="btn btn-ghost btn-sm" onClick={() => navigate("/")}>
              <ArrowLeft size={14} className="me-1" /> Back to home
            </button>
          </div>
          <div className="mb-4">
            <h4 style={{ fontWeight: 700 }}>{otpStage ? "One-time verification" : "Login"}</h4>
            <p className="text-soft mb-0" style={{ fontSize: "0.9rem" }}>
              {otpStage
                ? "Enter the code sent by the server to finish signing in."
                : accountType === "admin"
                ? "Administrator sign-in uses your Django username or email and a one-time verification code."
                : "Voter sign-in uses the registered voter email and password. Voter authentication requires the voter-login API."}
            </p>
          </div>

          {expiredNotice && !otpStage && (
            <Alert variant="warning" className="mb-3" onDismiss={clearSessionNotice}>
              {expiredNotice}
            </Alert>
          )}
          {error && <Alert variant="danger" className="mb-3">{error}</Alert>}
          {otpMessage && otpStage && <Alert variant="info" className="mb-3">{otpMessage}</Alert>}

          {!DEMO_MODE && accountType === "voter" && !otpStage && (
            <Alert variant="warning" className="mb-3">
              The uploaded Django backend currently implements administrator OTP login only. The voter login screen is ready, but it requires the backend to add <code>/api/voter/login</code> before production use.
            </Alert>
          )}

          {DEMO_MODE && (
            <div className="demo-hint mb-3">
              <strong>Demo accounts</strong> (sample data, not real credentials):
              <div className="mt-2">
                Admin — <code>{DEMO_CREDENTIALS.admin.identifier}</code> / <code>{DEMO_CREDENTIALS.admin.password}</code> · OTP <code>{DEMO_CREDENTIALS.admin.otp}</code>
              </div>
              <div>
                Voter — <code>{DEMO_CREDENTIALS.voter.identifier}</code> / <code>{DEMO_CREDENTIALS.voter.password}</code>
              </div>
              <div>
                Voter (already voted) — <code>{DEMO_CREDENTIALS.voter2.identifier}</code> / <code>{DEMO_CREDENTIALS.voter2.password}</code>
              </div>
            </div>
          )}

          {!otpStage ? (
            <form onSubmit={handleLogin} noValidate>
              <div className="d-flex gap-2 mb-3" role="group" aria-label="Account type">
                <button type="button" className={`btn btn-sm flex-fill ${accountType === "admin" ? "btn-primary" : "btn-ghost"}`} onClick={() => { setAccountType("admin"); setError(null); }}>Administrator</button>
                <button type="button" className={`btn btn-sm flex-fill ${accountType === "voter" ? "btn-primary" : "btn-ghost"}`} onClick={() => { setAccountType("voter"); setError(null); }}>Voter</button>
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="identifier">{accountType === "admin" ? "Administrator username or email" : "Registered voter email / ID"}</label>
                <input
                  id="identifier"
                  type="text"
                  className="form-control"
                  placeholder={accountType === "admin" ? "admin username or admin@example.org" : "voter@example.org"}
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  autoComplete="username"
                  disabled={busy}
                />
              </div>
              <div className="mb-4">
                <label className="form-label" htmlFor="password">Password</label>
                <div className="input-group">
                  <input
                    id="password"
                    type={showPw ? "text" : "password"}
                    className="form-control"
                    placeholder="Your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    disabled={busy}
                  />
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ padding: "0.55rem 0.85rem" }}
                    onClick={() => setShowPw((s) => !s)}
                    aria-label={showPw ? "Hide password" : "Show password"}
                  >
                    {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>
              <button type="submit" className="btn btn-primary w-100" disabled={busy}>
                {busy ? <span className="spinner-ring" /> : <KeyRound size={16} className="me-1" />}
                <span className="ms-1">{busy ? "Verifying…" : accountType === "admin" ? "Admin sign in" : "Voter sign in"}</span>
              </button>
              <div className="text-center mt-3">
                <Link to="/" style={{ fontSize: "0.84rem" }}>Return to home page</Link>
              </div>
            </form>
          ) : (
            <form onSubmit={handleOtp} noValidate>
              <div className="mb-4">
                <label className="form-label" htmlFor="otp">6-digit code</label>
                <input
                  id="otp"
                  className="form-control text-center"
                  style={{ letterSpacing: "0.5em", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: "1.2rem" }}
                  inputMode="numeric"
                  maxLength={8}
                  placeholder="••••••"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                  disabled={busy}
                  autoFocus
                />
                {DEMO_MODE && <div className="text-faint mt-2" style={{ fontSize: "0.78rem" }}>Demo code: <code className="inline">{DEMO_CREDENTIALS.admin.otp}</code> (in production the code is delivered by the backend)</div>}
              </div>
              <button type="submit" className="btn btn-primary w-100" disabled={busy}>
                {busy ? <span className="spinner-ring" /> : <ShieldCheck size={16} className="me-1" />}
                <span className="ms-1">{busy ? "Verifying code…" : "Verify & continue"}</span>
              </button>
              <div className="text-center mt-3">
                <button type="button" className="btn border-0 bg-transparent text-soft" style={{ fontSize: "0.84rem" }} onClick={() => { setOtpStage(false); setOtpMessage(null); setError(null); }}>
                  ← Back to login
                </button>
              </div>
            </form>
          )}

          <div className="d-flex align-items-center gap-2 mt-4 pt-3" style={{ borderTop: "1px solid var(--line)", fontSize: "0.76rem", color: "var(--ink-faint)", fontWeight: 600 }}>
            <Server size={13} />
            {DEMO_MODE ? "Demo mode: simulated responses in the browser" : "Connected to your Django REST backend"}
          </div>
        </div>
      </div>
    </div>
  );
}
