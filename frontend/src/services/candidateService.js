import { request, API_PATHS, asList, DEMO_MODE } from "./api";

const fromBackend = (c) => ({ ...c, election_id: c.election ?? c.election_id });
const toBackend = (payload) => DEMO_MODE ? ({
  name: payload.name,
  election_id: Number(payload.election_id ?? payload.election),
  description: payload.description || "",
}) : ({
  name: payload.name,
  election: Number(payload.election_id ?? payload.election),
  description: payload.description || "",
});

export const listCandidates = async (electionId) => {
  const rows = asList(await request(API_PATHS.candidates)).map(fromBackend);
  return electionId ? rows.filter((c) => String(c.election_id) === String(electionId)) : rows;
};

export const createCandidate = (payload) =>
  request(API_PATHS.candidates, { method: "post", data: toBackend(payload) });

export const updateCandidate = (id, payload) =>
  request(API_PATHS.candidate(id), { method: "patch", data: toBackend(payload) });

export const deleteCandidate = (id) =>
  request(API_PATHS.candidate(id), { method: "delete" });
