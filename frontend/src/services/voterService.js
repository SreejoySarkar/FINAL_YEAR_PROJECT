import { request, API_PATHS, asList, DEMO_MODE } from "./api";

export const listVoters = async (search) => {
  const rows = asList(await request(API_PATHS.voters));
  const mapped = rows.map((v) => ({
    ...v,
    voter_id: v.voter_code || v.voter_id,
    name: v.full_name || v.name,
    is_eligible: v.is_active ?? v.is_eligible,
    has_voted_elections: v.has_voted_elections || [],
    voting_status: Array.isArray(v.has_voted_elections) && v.has_voted_elections.length
      ? `Voted in ${v.has_voted_elections.length} election(s)`
      : DEMO_MODE ? "Not voted" : "Not reported by backend",
  }));
  if (!search) return mapped;
  const q = search.toLowerCase();
  return mapped.filter((v) =>
    [v.voter_id, v.name, v.email, v.department].some((x) => String(x || "").toLowerCase().includes(q))
  );
};

export const createVoter = (voter) =>
  request(API_PATHS.voters, {
    method: "post",
    data: DEMO_MODE ? {
      voter_id: voter.voter_id,
      name: voter.name,
      email: voter.email,
      department: voter.department || "",
      is_eligible: voter.is_eligible !== false,
    } : {
      voter_code: voter.voter_id,
      full_name: voter.name,
      email: voter.email,
      department: voter.department || "",
      is_active: voter.is_eligible !== false,
    },
  });

export const assignVotersToElection = (electionId, voterIds) => {
  const ids = voterIds.map(Number);
  if (!Number.isInteger(Number(electionId)) || Number(electionId) <= 0) throw new Error("Select a valid election.");
  if (!ids.length || ids.some((id) => !Number.isInteger(id) || id <= 0)) throw new Error("Select at least one valid voter.");
  return request(`/api/elections/${electionId}/eligible-voters`, {
    method: "post",
    data: { voter_ids: ids },
  });
};

export const listElectionEligibility = async (electionId) =>
  asList(await request(`/api/elections/${electionId}/eligible-voters`));
