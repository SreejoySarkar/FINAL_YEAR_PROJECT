/** Shared API route definitions and demo delay helper.
 * Kept separate from api.js to avoid a circular dependency with mockBackend.js.
 */
export const API_PATHS = {
  // Authentication
  login: "/api/admin/login",
  voterLogin: "/api/voter/login",
  otpVerify: "/api/admin/verify-otp",
  logout: "/api/admin/logout",
  me: "/api/auth/me",

  // Admin
  adminStats: "/api/admin/stats",
  elections: "/api/elections/",
  election: (id) => `/api/elections/${id}/`,
  candidates: "/api/candidates/",
  candidate: (id) => `/api/candidates/${id}/`,
  voters: "/api/voters/",
  qrGenerate: "/api/qr/generate/",
  qrGenerateForElection: (id) => `/api/elections/${id}/generate-qr`,
  auditLogs: "/api/audit-logs",
  auditVerify: "/api/audit-logs/verify",

  // Shared / voter
  qrVerify: "/api/qr/verify/",
  results: (id) => `/api/elections/${id}/results/`,
  vote: (id) => `/api/elections/${id}/vote/`,
  voterElections: "/api/voter/elections/",
  electionCandidates: (id) => `/api/elections/${id}/candidates`,
};

export const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
