export function Spinner({ dark = false, size = "md" }) {
  return <span className={`spinner-ring ${dark ? "dark" : ""}`} style={size === "sm" ? { width: 16, height: 16, borderWidth: 2 } : undefined} aria-label="Loading" />;
}

export default function PageLoading({ label = "Loading…" }) {
  return (
    <div className="page-loading">
      <Spinner dark />
      <div className="text-soft" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
        {label}
      </div>
    </div>
  );
}
