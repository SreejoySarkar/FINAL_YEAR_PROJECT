import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Vote, Users, QrCode, ScrollText, BarChart3, LogOut, ShieldCheck, X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { initials, avatarColor } from "./ui";
import { DEMO_MODE } from "../services/api";

const ADMIN_LINKS = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/elections", label: "Manage Elections", icon: Vote },
  { to: "/admin/candidates", label: "Manage Candidates", icon: Users },
  { to: "/admin/voters", label: "Manage Voters", icon: Users },
  { to: "/admin/qr", label: "QR Code Management", icon: QrCode },
  { to: "/admin/audit", label: "Audit Logs", icon: ScrollText },
  { to: "/admin/results", label: "Election Results", icon: BarChart3 },
];

const VOTER_LINKS = [{ to: "/vote", label: "My Elections", icon: Vote, end: true }];

export default function Sidebar() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const links = role === "admin" ? ADMIN_LINKS : VOTER_LINKS;

  const onLogout = async () => {
    setOpen(false);
    await logout();
  };

  return (
    <>
      {open && <div className="sidebar-backdrop" onClick={() => setOpen(false)} />}
      <aside className={`sidebar ${open ? "open" : ""}`} aria-label="Main navigation">
        <div className="sidebar-brand">
          <span className="brand-mark">
            <ShieldCheck size={22} strokeWidth={2.2} />
          </span>
          <div>
            <div className="brand-name">Secure E-Voting</div>
            <div className="brand-sub">{role === "admin" ? "Admin Console" : "Voter Portal"}</div>
          </div>
          <button
            className="btn d-lg-none ms-auto border-0"
            style={{ color: "#9fb2cb", padding: "0.25rem" }}
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <div className="side-label">Menu</div>
          {links.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setOpen(false)}
              className={({ isActive }) => `side-link ${isActive ? "active" : ""}`}
            >
              <Icon size={18} className="side-icon" />
              {label}
            </NavLink>
          ))}

          <div className="side-label">Session</div>
          <button className="side-link w-100" style={{ background: "transparent", border: "none", width: "100%", textAlign: "left" }} onClick={onLogout}>
            <LogOut size={18} className="side-icon" />
            Logout
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="avatar avatar-sm" style={{ background: avatarColor(user?.name || "") }}>
              {initials(user?.name || "")}
            </span>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div className="name text-truncate">{user?.name || "—"}</div>
              <div className="meta">{role === "admin" ? "Administrator" : `Voter ${user?.voter_id || ""}`}</div>
            </div>
            {!DEMO_MODE && <span className="badge badge-green" style={{ fontSize: "0.62rem" }}>LIVE</span>}
            {DEMO_MODE && <span className="badge badge-warn" style={{ fontSize: "0.62rem" }}>DEMO</span>}
          </div>
          <button
            className="btn btn-ghost w-100 mt-2 btn-sm"
            style={{ justifyContent: "center", background: "rgba(255,255,255,0.06)", borderColor: "rgba(255,255,255,0.15)", color: "#c6d3e6" }}
            onClick={() => {
              setOpen(false);
              navigate("/");
            }}
          >
            Back to site
          </button>
        </div>
      </aside>
    </>
  );
}
