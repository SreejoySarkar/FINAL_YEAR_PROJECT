import { useState } from "react";
import { Menu } from "lucide-react";
import Sidebar from "./Sidebar";
import { DEMO_MODE } from "../services/api";

export default function DashboardLayout({ crumb, title, actions, children, wide = false }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="shell">
      <Sidebar />
      <div className="main-col">
        <header className="topbar">
          <button
            className="btn btn-ghost d-lg-none"
            style={{ padding: "0.35rem 0.55rem" }}
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={19} />
          </button>
          <div style={{ minWidth: 0 }}>
            <div className="crumb">{crumb}</div>
            <h1 className="text-truncate">{title}</h1>
          </div>
          <div className="ms-auto d-flex align-items-center gap-2">
            {actions}
            <span className={`conn-chip ${DEMO_MODE ? "demo" : "live"}`}>
              <span className="pulse" />
              {DEMO_MODE ? "DEMO DATA" : "LIVE API"}
            </span>
          </div>
        </header>
        <main className={`page-body ${wide ? "" : "container-fluid"}`}>{children}</main>
      </div>
    </div>
  );
}
