/**
 * In-memory ballot session state.
 *
 * Holds ONLY what is needed to complete the current voting flow (the
 * server-issued verification token and, after submission, the receipt
 * reference). It is deliberately kept in memory — never in localStorage or
 * sessionStorage — so no voting artefacts survive page reloads or share the
 * browser profile.
 */
let session = null; // { electionId, verificationToken, referenceId, voterId }

export const getBallotSession = () => session;

export const setBallotSession = (s) => {
  session = s;
};

export const clearBallotSession = () => {
  session = null;
};
