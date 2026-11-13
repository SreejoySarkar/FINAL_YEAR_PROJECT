import { useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  ShieldCheck, Lock, QrCode, EyeOff, Fingerprint, FileCheck2, ChevronRight,
  Landmark, KeyRound, ScanLine, ServerCog,
} from "lucide-react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import { DEMO_MODE } from "../services/api";
import { Alert } from "../components/ui";

const FEATURES = [
  {
    icon: Lock,
    title: "Secure authentication",
    text: "Role-based login with optional one-time codes. Sessions are short-lived and every request is re-checked by the backend.",
  },
  {
    icon: QrCode,
    title: "QR-based election access",
    text: "Election-specific access tokens are generated and signed by the backend, scanned at the booth and verified before any ballot opens.",
  },
  {
    icon: EyeOff,
    title: "Anonymous voting",
    text: "The system never links a voter to the candidate they chose. Admins can see that a ballot was cast — never which one.",
  },
  {
    icon: Fingerprint,
    title: "Duplicate-vote prevention",
    text: "Eligibility and prior ballots are validated server-side on every submission. Second attempts are rejected, not queued.",
  },
  {
    icon: FileCheck2,
    title: "Verifiable election results",
    text: "Results appear only after the election closes and the append-only audit trail verifies the seal. Nothing is computed client-side.",
  },
  {
    icon: Landmark,
    title: "Built for governance",
    text: "Board elections, AGM motions, staff councils and referendums — run them from one clean administrative console.",
  },
];

const STEPS = [
  { icon: KeyRound, title: "Register & authorise", text: "Administrators register elections, candidates and eligible voters in the console." },
  { icon: ScanLine, title: "Verify & enter", text: "Voters present an election-specific QR token. The backend verifies validity, expiry and eligibility." },
  { icon: ServerCog, title: "Ballot sealed & audited", text: "The vote is submitted to the server once. It is sealed, logged in the audit trail and counted only after closing." },
];

export default function Home() {
  const navigate = useNavigate();
  const location = useLocation();

  /* smooth-scroll when arriving from navbar/footer section links */
  useEffect(() => {
    const target = location.state?.scrollTo;
    if (target) {
      setTimeout(() => document.getElementById(target)?.scrollIntoView({ behavior: "smooth" }), 60);
    } else {
      window.scrollTo(0, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Navbar />

      {/* HERO */}
      <section className="hero" id="home">
        <div className="hero-grid" aria-hidden="true" />
        <div className="container py-5" style={{ position: "relative" }}>
          <div className="row g-5 align-items-center py-5">
            <div className="col-lg-7">
              <div className="d-flex align-items-center gap-2 mb-4">
                <span className="badge" style={{ background: "rgba(23,184,119,0.16)", color: "#45e0a2" }}>
                  <span className="badge-dot" style={{ background: "#45e0a2" }} />
                  Election integrity platform
                </span>
              </div>
              <h1 style={{ fontSize: "clamp(2rem, 4.6vw, 3.2rem)", lineHeight: 1.12, fontWeight: 700 }}>
                Secure, Transparent and <span className="text-green-accent">Reliable</span> Online Voting
              </h1>
              <p className="text-muted-2 mt-3" style={{ fontSize: "1.05rem", maxWidth: "56ch", lineHeight: 1.7 }}>
                Secure E-Voting System runs board elections, AGM polls and referendums end to end:
                verified voter access, anonymous ballots, duplicate-vote protection and
                audit-verified results — all enforced by the backend, never by the browser.
              </p>
              <div className="d-flex gap-3 flex-wrap mt-4">
                <Link to="/login" className="btn btn-accent btn-lg px-4">
                  Log in to vote <ChevronRight size={17} className="ms-1" />
                </Link>
                <Link to="/login" className="btn btn-outline-light-2 btn-lg px-4">
                  Administrator console
                </Link>
              </div>
              <div className="d-flex flex-wrap gap-3 mt-4" style={{ fontSize: "0.82rem", color: "#8fa4c2", fontWeight: 600 }}>
                <span className="d-flex align-items-center gap-2"><ShieldCheck size={15} className="text-green-accent" /> Backend-authorised access</span>
                <span className="d-flex align-items-center gap-2"><QrCode size={15} className="text-green-accent" /> Signed QR tokens</span>
                <span className="d-flex align-items-center gap-2"><EyeOff size={15} className="text-green-accent" /> Anonymous ballots</span>
              </div>
            </div>
            <div className="col-lg-5">
              <div className="row g-3">
                <div className="col-6">
                  <div className="login-tile">
                    <div className="icon-chip mb-3" style={{ background: "rgba(23,184,119,0.18)", color: "#45e0a2" }}>
                      <ShieldCheck size={22} />
                    </div>
                    <div style={{ fontWeight: 800, fontFamily: "var(--font-display)" }}>Administrator</div>
                    <p className="mt-1" style={{ fontSize: "0.82rem", color: "#9fb2cb", marginBottom: "1rem" }}>
                      Run elections, manage voters and verify audit trails.
                    </p>
                    <Link to="/login" className="btn btn-outline-light-2 btn-sm">Admin login</Link>
                  </div>
                </div>
                <div className="col-6">
                  <div className="login-tile">
                    <div className="icon-chip mb-3" style={{ background: "rgba(255,255,255,0.1)", color: "#cfe0f5" }}>
                      <Fingerprint size={22} />
                    </div>
                    <div style={{ fontWeight: 800, fontFamily: "var(--font-display)" }}>Voter</div>
                    <p className="mt-1" style={{ fontSize: "0.82rem", color: "#9fb2cb", marginBottom: "1rem" }}>
                      Verify access by QR and cast a single anonymous ballot.
                    </p>
                    <Link to="/login" className="btn btn-accent btn-sm">Voter login</Link>
                  </div>
                </div>
                <div className="col-12">
                  <div className="login-tile d-flex align-items-center gap-3">
                    <FileCheck2 size={26} className="text-green-accent flex-shrink-0" />
                    <div>
                      <div style={{ fontWeight: 700, fontFamily: "var(--font-display)", fontSize: "0.92rem" }}>
                        Results only when verified
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "#9fb2cb" }}>
                        Counts are sealed until the audit trail confirms the election is closed.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="py-5" id="features" style={{ background: "var(--paper)" }}>
        <div className="container py-4">
          <div className="row mb-4">
            <div className="col-lg-7">
              <div className="eyebrow mb-2">Why teams trust it</div>
              <h2 className="section-title" style={{ fontSize: "clamp(1.5rem, 3vw, 2.1rem)" }}>
                Everything an election needs. Nothing that leaks.
              </h2>
              <p className="text-soft mt-2" style={{ maxWidth: "58ch" }}>
                Every security-critical operation — authentication, token signing, eligibility,
                duplicate checks and result publication — happens on the Django backend.
              </p>
            </div>
          </div>
          <div className="row g-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <div className="col-12 col-md-6 col-lg-4" key={title}>
                <div className="feature-card">
                  <div className="icon-chip mb-3" style={{ background: "var(--green-100)", color: "var(--green-600)" }}>
                    <Icon size={22} />
                  </div>
                  <h6 style={{ fontWeight: 700, fontSize: "1rem" }}>{title}</h6>
                  <p className="text-soft mb-0" style={{ fontSize: "0.88rem", lineHeight: 1.6 }}>{text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-5" style={{ background: "var(--surface)", borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)" }}>
        <div className="container py-4">
          <div className="eyebrow mb-2">How a ballot travels</div>
          <h2 className="section-title mb-4" style={{ fontSize: "clamp(1.4rem, 2.6vw, 1.9rem)" }}>Three steps, fully server-verified</h2>
          <div className="row g-4">
            {STEPS.map(({ icon: Icon, title, text }, i) => (
              <div className="col-12 col-md-4" key={title}>
                <div className="d-flex gap-3">
                  <div className="text-center flex-none" style={{ width: 54 }}>
                    <div className="icon-chip" style={{ background: "var(--navy-900)", color: "#45e0a2", width: 48, height: 48, borderRadius: 12 }}>
                      <Icon size={21} />
                    </div>
                    <div className="text-faint mt-2" style={{ fontSize: "0.72rem", fontWeight: 800, letterSpacing: "0.1em" }}>STEP {i + 1}</div>
                  </div>
                  <div>
                    <h6 style={{ fontWeight: 700 }}>{title}</h6>
                    <p className="text-soft mb-0" style={{ fontSize: "0.88rem", lineHeight: 1.6 }}>{text}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section className="py-5" id="about">
        <div className="container py-4">
          <div className="row g-4 align-items-center">
            <div className="col-lg-6">
              <div className="eyebrow mb-2">About the platform</div>
              <h2 className="section-title mb-3" style={{ fontSize: "clamp(1.4rem, 2.6vw, 1.9rem)" }}>
                An election system that shows its work
              </h2>
              <p className="text-soft" style={{ lineHeight: 1.75 }}>
                Secure E-Voting System pairs a professional React interface with a
                Django REST Framework backend on PostgreSQL. Administrators manage the full
                election lifecycle; voters get a calm, single-purpose ballot experience.
                Every sensitive decision is made by the server, and every significant action
                is recorded in an append-only audit log that administrators can review.
              </p>
              <ul className="list-unstyled d-grid gap-2 mt-3" style={{ fontSize: "0.92rem" }}>
                {["Roles enforced by backend authorization, not by the browser", "QR tokens generated, signed and expired server-side", "Vote receipts reference a ballot — never reveal a candidate", "Result publication gated on verification status"].map((t) => (
                  <li key={t} className="d-flex gap-2 align-items-start">
                    <ShieldCheck size={17} className="text-green-accent mt-1" style={{ color: "var(--green-600)" }} />
                    <span className="text-soft">{t}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="col-lg-6">
              {DEMO_MODE ? (
                <Alert variant="warning" className="mb-3">
                  <strong>Demo mode.</strong> No backend URL is configured, so the pages below run on
                  clearly-labelled sample data. Point <code className="inline">VITE_API_BASE_URL</code> at
                  your Django server for live data.
                </Alert>
              ) : null}
              <div className="card p-4">
                <div className="d-flex align-items-center gap-3 mb-3">
                  <span className="icon-chip" style={{ background: "var(--navy-900)", color: "#45e0a2" }}>
                    <Landmark size={20} />
                  </span>
                  <div>
                    <div style={{ fontWeight: 800, fontFamily: "var(--font-display)" }}>Ready to run your next election?</div>
                    <div className="text-faint" style={{ fontSize: "0.82rem" }}>Both roles sign in on the same secure login page.</div>
                  </div>
                </div>
                <div className="d-flex gap-2 flex-wrap">
                  <button className="btn btn-primary" onClick={() => navigate("/login")}>Open the login page</button>
                  <button className="btn btn-ghost" onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}>Review security features</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
