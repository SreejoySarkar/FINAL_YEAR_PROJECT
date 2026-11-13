import { useState, useRef, useCallback } from "react";
import { AlertTriangle, CheckCircle2, XCircle, Info, X } from "lucide-react";
import { DEMO_MODE } from "../services/api";

/* ---------- status badge ---------- */
const STATUS_MAP = {
  active: { cls: "badge-green", label: "Active", dot: "var(--green-500)" },
  upcoming: { cls: "badge-navy", label: "Upcoming", dot: "var(--navy-700)" },
  closed: { cls: "badge-muted", label: "Closed", dot: "#8b98ab" },
  draft: { cls: "badge-warn", label: "Draft", dot: "var(--warn-600)" },
  valid: { cls: "badge-green", label: "Valid", dot: "var(--green-500)" },
  used: { cls: "badge-muted", label: "Used", dot: "#8b98ab" },
  expired: { cls: "badge-red", label: "Expired", dot: "var(--danger-600)" },
};

export function StatusBadge({ status, label }) {
  const s = STATUS_MAP[status] || { cls: "badge-muted", label: status || "—", dot: "#8b98ab" };
  return (
    <span className={`badge ${s.cls}`}>
      <span className="badge-dot" style={{ background: s.dot }} />
      {label || s.label}
    </span>
  );
}

/* ---------- inline alert ---------- */
const ALERT_ICON = { success: CheckCircle2, danger: XCircle, warning: AlertTriangle, info: Info };
const ALERT_BORDER = { success: "alert-success", danger: "alert-danger", warning: "alert-warning", info: "alert-info" };

export function Alert({ variant = "info", children, onDismiss, className = "" }) {
  const Icon = ALERT_ICON[variant] || Info;
  return (
    <div className={`alert ${ALERT_BORDER[variant]} d-flex align-items-start gap-2 ${className}`} role="alert">
      <Icon size={18} className="flex-shrink-0 mt-1" />
      <div className="flex-grow-1">{children}</div>
      {onDismiss && (
        <button className="btn-close" style={{ fontSize: "0.6rem" }} onClick={onDismiss} aria-label="Dismiss" />
      )}
    </div>
  );
}

/* ---------- modal ---------- */
export function Modal({ title, onClose, children, footer, wide = false }) {
  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}>
      <div className={`modal-panel ${wide ? "wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head">
          <h5>{title}</h5>
          <button className="modal-x" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body-pad">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

export function ConfirmModal({ title, message, confirmLabel = "Confirm", variant = "primary", busy = false, onConfirm, onCancel }) {
  return (
    <Modal
      title={title}
      onClose={busy ? undefined : onCancel}
      footer={
        <>
          <button className="btn btn-ghost" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button className={`btn btn-${variant}`} onClick={onConfirm} disabled={busy}>
            {busy ? <Spinner2 /> : null}
            <span className="ms-1">{confirmLabel}</span>
          </button>
        </>
      }
    >
      <p className="text-soft mb-0">{message}</p>
    </Modal>
  );
}

function Spinner2() {
  return <span className="spinner-ring" style={{ width: 15, height: 15, borderWidth: 2 }} />;
}

/* ---------- page header ---------- */
export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="page-head">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children && <div className="d-flex gap-2 flex-wrap align-items-center">{children}</div>}
    </div>
  );
}

/* ---------- stat / KPI card ---------- */
export function StatCard({ icon: Icon, label, value, tone = "navy", hint }) {
  return (
    <div className="kpi-card">
      {Icon && (
        <div className={`kpi-icon ${tone}`}>
          <Icon size={22} />
        </div>
      )}
      <div style={{ minWidth: 0 }}>
        <div className="small-caps">{label}</div>
        <div className="kpi-value mt-1">{value ?? "—"}</div>
        {hint && <div className="text-faint" style={{ fontSize: "0.75rem", marginTop: 2 }}>{hint}</div>}
      </div>
    </div>
  );
}

/* ---------- empty state ---------- */
export function EmptyState({ icon: Icon, title, text, children }) {
  return (
    <div className="text-center py-5 px-3">
      {Icon && (
        <div style={{ width: 52, height: 52, borderRadius: 14, background: "var(--navy-100)", color: "var(--navy-800)", display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: "0.9rem" }}>
          <Icon size={24} />
        </div>
      )}
      <h6 style={{ fontWeight: 700 }}>{title}</h6>
      {text && <p className="text-soft mb-3" style={{ fontSize: "0.9rem", maxWidth: "46ch", margin: "0 auto 1rem" }}>{text}</p>}
      {children}
    </div>
  );
}

/* ---------- demo-mode banner ---------- */
export function DemoBanner() {
  if (!DEMO_MODE) return null;
  return (
    <div className="demo-banner py-2 px-3 text-center d-flex align-items-center justify-content-center gap-2 flex-wrap">
      <AlertTriangle size={14} />
      <span>
        <strong>DEMO MODE</strong> — sample data in the browser only. Not connected to the Django backend; no real votes or results.
      </span>
    </div>
  );
}

/* ---------- lightweight toast ---------- */
export function useToast() {
  const [toast, setToast] = useState(null);
  const timer = useRef(null);
  const show = useCallback((message, type = "success") => {
    setToast({ message, type });
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setToast(null), 4200);
  }, []);
  const dismiss = useCallback(() => setToast(null), []);
  return { toast, show, dismiss };
}

export function Toast({ toast, onDismiss }) {
  if (!toast) return null;
  const Icon = toast.type === "error" ? XCircle : CheckCircle2;
  return (
    <div className={`toast-app ${toast.type === "error" ? "error" : "success"}`}>
      <Icon size={18} className="mt-05" style={{ marginTop: 2, flexShrink: 0 }} />
      <div style={{ flex: 1 }}>{toast.message}</div>
      <button className="btn border-0 bg-transparent text-white p-0" style={{ opacity: 0.7 }} onClick={onDismiss} aria-label="Dismiss">
        <X size={15} />
      </button>
    </div>
  );
}

/* ---------- avatar helper ---------- */
const AVATAR_HUES = [222, 158, 262, 20, 340, 190];
export function initials(name = "") {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("") || "?";
}
export function avatarColor(name = "") {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) % 997;
  return `hsl(${AVATAR_HUES[h % AVATAR_HUES.length]} 45% 38%)`;
}
