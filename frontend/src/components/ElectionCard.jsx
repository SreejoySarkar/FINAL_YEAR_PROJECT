import { CalendarDays, Users, Eye, Pencil, Trash2, QrCode } from "lucide-react";
import { StatusBadge } from "./ui";
import { formatDate } from "../services/electionService";

/**
 * Card for one election in the admin area.
 * Actions (edit/delete/qr) are only rendered when handlers are supplied —
 * the backend still performs the real authorization for each operation.
 */
export default function ElectionCard({ election, onView, onEdit, onDelete, onQr }) {
  const e = election;
  return (
    <div className="election-card card-hover">
      <div className="top">
        <div className="d-flex justify-content-between align-items-start gap-2 mb-2">
          <StatusBadge status={e.status} />
          <span className="text-faint" style={{ fontSize: "0.75rem", fontWeight: 700 }}>
            #{e.id}
          </span>
        </div>
        <h5 style={{ fontWeight: 700, fontSize: "1.06rem", marginBottom: "0.4rem" }}>{e.title}</h5>
        {e.description && (
          <p className="text-soft" style={{ fontSize: "0.87rem", marginBottom: "0.9rem", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {e.description}
          </p>
        )}
        <div className="d-flex flex-column gap-1" style={{ fontSize: "0.83rem", color: "var(--ink-soft)" }}>
          <span className="d-flex align-items-center gap-2">
            <CalendarDays size={15} className="text-faint" />
            {formatDate(e.starts_at)} → {formatDate(e.ends_at)}
          </span>
          <span className="d-flex align-items-center gap-2">
            <Users size={15} className="text-faint" />
            {e.candidates_count ?? "—"} candidates
            {typeof e.votes_cast === "number" && <span className="text-faint">· {e.votes_cast} ballots cast</span>}
          </span>
        </div>
      </div>
      {(onView || onEdit || onDelete || onQr) && (
        <div className="foot">
          <div className="d-flex gap-2 flex-wrap">
            {onView && (
              <button className="btn btn-primary btn-sm" onClick={() => onView(e)}>
                <Eye size={14} className="me-1" /> View
              </button>
            )}
            {onQr && (
              <button className="btn btn-ghost btn-sm" onClick={() => onQr(e)} title="Generate QR access token">
                <QrCode size={14} className="me-1" /> QR
              </button>
            )}
            {onEdit && (
              <button className="btn btn-ghost btn-sm" onClick={() => onEdit(e)}>
                <Pencil size={14} className="me-1" /> Edit
              </button>
            )}
            {onDelete && (
              <button className="btn btn-danger-soft btn-sm" onClick={() => onDelete(e)}>
                <Trash2 size={14} className="me-1" /> Delete
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
