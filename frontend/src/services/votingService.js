import { request, API_PATHS, asList } from "./api";

/** Elections the authenticated voter may see (backend filters eligibility). */
export const listMyElections = async () => asList(await request(API_PATHS.voterElections)).map((e) => ({
  ...e,
  starts_at: e.start_time || e.starts_at,
  ends_at: e.end_time || e.ends_at,
  status: e.status === "published" ? "active" : e.status,
  eligible: e.eligible ?? e.is_eligible ?? false,
  has_voted: e.has_voted ?? e.voted ?? false,
}));

/**
 * Submit a ballot. The backend performs all validation (eligibility,
 * duplicate-vote prevention, token single-use, candidate membership) and
 * returns a receipt reference. The chosen candidate is never stored in the
 * browser — only in memory, for the duration of this request.
 */
export const submitVote = (electionId, { candidateId, verificationToken }) =>
  request(API_PATHS.vote(electionId), {
    method: "post",
    data: { candidate_id: candidateId, verification_token: verificationToken },
  });
