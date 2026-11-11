import { Pencil, Trash2 } from "lucide-react";
import { initials, avatarColor } from "./ui";

/**
 * Candidate card with two modes:
 *  - mode="admin": management view with edit/delete actions
 *  - mode="ballot": selectable radio row used on the voting page
 */
export default function CandidateCard({
  candidate,
  electionLabel,
  mode = "admin",
  selected = false,
  disabled = false,
  onSelect,
  onEdit,
  onDelete,
  name = "candidate",
}) {
  const c = candidate;

  if (mode === "ballot") {
    return (
      <label className={`candidate-card cursor-pointer ${selected ? "selected" : ""}`} style={{ cursor: disabled ? "not-allowed" : "pointer" }}>
        <input
          type="radio"
          name={name}
          className="form-check-input"
          checked={selected}
          disabled={disabled}
          onChange={() => onSelect?.(c)}
        />
        <span className="cand-photo" style={{ background: c.photo ? "transparent" : avatarColor(c.name) }}>
          {c.photo ? <img src={c.photo} alt={c.name} /> : initials(c.name)}
        </span>
        <span style={{ minWidth: 0, paddingRight: "2.2rem" }}>
          <span className="d-block" style={{ fontWeight: 800, fontFamily: "var(--font-display)", fontSize: "1rem" }}>
            {c.name}
          </span>
          {c.role && <span className="d-block text-faint" style={{ fontSize: "0.78rem", fontWeight: 700 }}>{c.role}</span>}
          {c.description && (
            <span className="d-block text-soft mt-1" style={{ fontSize: "0.86rem", lineHeight: 1.5 }}>
              {c.description}
            </span>
          )}
        </span>
      </label>
    );
  }

  return (
    <div className="card card-hover" style={{ overflow: "hidden" }}>
      <div className="card-body" style={{ display: "flex", gap: "0.9rem", alignItems: "flex-start" }}>
        <span className="cand-photo" style={{ background: c.photo ? "transparent" : avatarColor(c.name) }}>
          {c.photo ? <img src={c.photo} alt={c.name} /> : initials(c.name)}
        </span>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="d-flex justify-content-between align-items-start gap-2">
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 800, fontFamily: "var(--font-display)" }}>{c.name}</div>
              {c.role && <div className="text-faint" style={{ fontSize: "0.78rem", fontWeight: 700 }}>{c.role}</div>}
            </div>
            {(onEdit || onDelete) && (
              <div className="d-flex gap-1 flex-none">
                {onEdit && (
                  <button className="btn btn-ghost btn-sm" style={{ padding: "0.3rem 0.5rem" }} onClick={() => onEdit(c)} title="Edit candidate">
                    <Pencil size={14} />
                  </button>
                )}
                {onDelete && (
                  <button className="btn btn-danger-soft btn-sm" style={{ padding: "0.3rem 0.5rem" }} onClick={() => onDelete(c)} title="Delete candidate">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
          {c.description && <p className="text-soft mb-2 mt-2" style={{ fontSize: "0.86rem", lineHeight: 1.5 }}>{c.description}</p>}
          {electionLabel && <span className="badge badge-navy">{electionLabel}</span>}
        </div>
      </div>
    </div>
  );
}
