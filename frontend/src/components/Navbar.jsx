import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { ShieldCheck, LogIn, Menu, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function BrandMark({ size = 38 }) {
  return (
    <span className="brand-mark" style={{ width: size, height: size, borderRadius: size * 0.28 }}>
      <ShieldCheck size={size * 0.58} strokeWidth={2.2} />
    </span>
  );
}

export default function Navbar() {
  const { user, role } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  const goSection = (id) => {
    setOpen(false);
    if (location.pathname === "/") {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    } else {
      navigate("/", { state: { scrollTo: id } });
    }
  };

  return (
    <nav className="navbar nav-dark sticky-top py-3">
      <div className="container">
        <Link to="/" className="navbar-brand d-flex align-items-center gap-2 text-white" style={{ textDecoration: "none" }}>
          <BrandMark />
          <span className="brand-name" style={{ fontSize: "1.05rem" }}>
            Secure E-Voting <span className="text-green-accent">System</span>
          </span>
        </Link>
        <button
          className="btn btn-sm btn-outline-light-2 d-lg-none"
          style={{ padding: "0.4rem 0.6rem" }}
          onClick={() => setOpen((o) => !o)}
          aria-label="Toggle navigation"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
        <div className={`${open ? "show" : "d-none"} d-lg-flex align-items-center flex-grow-1 justify-content-end flex-wrap gap-1`}>
          <ul className="navbar-nav ms-auto align-items-lg-center gap-1">
            <li className="nav-item">
              <button type="button" className="nav-link border-0 bg-transparent" onClick={() => goSection("home")}>Home</button>
            </li>
            <li className="nav-item">
              <button type="button" className="nav-link border-0 bg-transparent" onClick={() => goSection("about")}>About</button>
            </li>
            <li className="nav-item">
              <button type="button" className="nav-link border-0 bg-transparent" onClick={() => goSection("features")}>Features</button>
            </li>
            {user ? (
              <li className="nav-item ms-lg-2">
                <button
                  className="btn btn-accent btn-sm"
                  onClick={() => navigate(role === "admin" ? "/admin" : "/vote")}
                >
                  My Dashboard
                </button>
              </li>
            ) : (
              <li className="nav-item ms-lg-2">
                <Link to="/login" className="btn btn-accent btn-sm d-inline-flex align-items-center gap-2">
                  <LogIn size={15} /> Login
                </Link>
              </li>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}
