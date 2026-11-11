import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { BrandMark } from "./Navbar";

export default function Footer() {
  return (
    <footer className="footer-dark pt-5 pb-4 mt-auto">
      <div className="container">
        <div className="row g-4">
          <div className="col-12 col-md-5">
            <div className="d-flex align-items-center gap-2 mb-3">
              <BrandMark size={34} />
              <span className="brand-name" style={{ color: "#fff" }}>Secure E-Voting System</span>
            </div>
            <p style={{ fontSize: "0.88rem", maxWidth: "42ch", lineHeight: 1.65 }}>
              A secure, transparent and reliable platform for online elections and
              corporate polling. Ballots are verified, sealed and audited by the
              backend — the interface only ever displays what the election
              authorities have published.
            </p>
          </div>
          <div className="col-6 col-md-3">
            <h5 className="mb-3">Platform</h5>
            <ul className="list-unstyled d-grid gap-2 mb-0">
              <li><Link to="/" state={{ scrollTo: "features" }}>Features</Link></li>
              <li><Link to="/" state={{ scrollTo: "about" }}>About the system</Link></li>
              <li><Link to="/login">Administrator login</Link></li>
              <li><Link to="/login">Voter login</Link></li>
            </ul>
          </div>
          <div className="col-6 col-md-4">
            <h5 className="mb-3">Project</h5>
            <ul className="list-unstyled d-grid gap-2 mb-0" style={{ fontSize: "0.9rem" }}>
              <li>Frontend: React · Bootstrap 5 · Axios</li>
              <li>Backend: Django REST Framework · PostgreSQL</li>
              <li>Access control: backend-enforced, role-based</li>
              <li className="d-flex align-items-center gap-2">
                <ShieldCheck size={15} className="text-green-accent" />
                Audit-verified results only
              </li>
            </ul>
          </div>
        </div>
        <hr style={{ borderColor: "rgba(255,255,255,0.1)", margin: "1.5rem 0 1rem" }} />
        <div className="d-flex flex-wrap justify-content-between gap-2" style={{ fontSize: "0.8rem" }}>
          <span>© 2026 Secure E-Voting System. For authorized electors and administrators only.</span>
          <span>Unauthorized access to election data is prohibited.</span>
        </div>
      </div>
    </footer>
  );
}
