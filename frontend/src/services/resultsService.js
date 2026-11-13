import { request, API_PATHS, asList, DEMO_MODE } from "./api";

export const getResults = async (electionId) => {
  // The UI is wired to this contract. The uploaded Django backend does not yet
  // register the endpoint, so a real-backend 404 is surfaced honestly to the UI.
  return request(API_PATHS.results(electionId));
};

export const getAuditLogs = async () => {
  const rows = asList(await request(API_PATHS.auditLogs));
  return rows.map((row) => {
    const action = row.action || "EVENT";
    const lower = action.toLowerCase();
    const category = lower.includes("login") || lower.includes("otp") ? "auth"
      : lower.includes("qr") ? "qr"
      : lower.includes("candidate") ? "candidate"
      : lower.includes("voter") ? "voter"
      : lower.includes("election") ? "election"
      : lower.includes("vote") || lower.includes("ballot") ? "vote"
      : "all";
    return {
      ...row,
      at: row.created_at || row.at,
      actor: row.actor_username || row.actor || "System",
      category: row.category || category,
      detail: row.details ? JSON.stringify(row.details) : (row.detail || ""),
      status: row.status || (action.toUpperCase().includes("FAILED") ? "failed" : "ok"),
    };
  });
};

export const verifyAuditChain = () => request(API_PATHS.auditVerify);
