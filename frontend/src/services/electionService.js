import { request, API_PATHS, asList, DEMO_MODE } from "./api";

const fromBackendElection = (e) => ({
  ...e,
  starts_at: e.start_time || e.starts_at,
  ends_at: e.end_time || e.ends_at,
  status: e.status === "published" ? "active" : e.status,
  candidates_count: e.candidates?.length ?? undefined,
});

const toBackendElection = (payload) => DEMO_MODE ? ({
  title: payload.title,
  description: payload.description || "",
  starts_at: payload.starts_at || payload.start_time,
  ends_at: payload.ends_at || payload.end_time,
  status: payload.status || "draft",
}) : ({
  title: payload.title,
  description: payload.description || "",
  eligibility_criteria: payload.eligibility_criteria || "",
  start_time: payload.starts_at || payload.start_time,
  end_time: payload.ends_at || payload.end_time,
});

export const listElections = async () =>
  asList(await request(API_PATHS.elections)).map(fromBackendElection);

export const getElection = async (id) =>
  fromBackendElection(await request(API_PATHS.election(id)));

export const createElection = (payload) =>
  request(API_PATHS.elections, { method: "post", data: toBackendElection(payload) });

export const updateElection = (id, payload) =>
  request(API_PATHS.election(id), { method: "patch", data: toBackendElection(payload) });

export const deleteElection = (id) =>
  request(API_PATHS.election(id), { method: "delete" });

export const listElectionCandidates = async (id) =>
  asList(await request(API_PATHS.electionCandidates(id))).map((c) => ({
    ...c,
    election_id: c.election,
  }));

export const toLocalInput = (value) => {
  if (!value) return "";
  const d = new Date(value);
  if (isNaN(d)) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

export const toIso = (value) => {
  if (!value) return null;
  const d = new Date(value);
  return isNaN(d) ? null : d.toISOString();
};

export const formatDate = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d)) return value;
  return d.toLocaleString(undefined, { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

export const formatDay = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d)) return value;
  return d.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
};

export const publishElection = (id) =>
  request(`${API_PATHS.election(id)}publish/`, { method: "post" });

export const closeElection = (id) =>
  request(`${API_PATHS.election(id)}close/`, { method: "post" });
