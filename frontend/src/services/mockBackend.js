/**
 * DEMO-ONLY in-memory backend.
 *
 * This module exists so the interface can be previewed WITHOUT the Django
 * server running (e.g. during UI development). It is only used when
 * VITE_API_BASE_URL is not configured. Everything here is simulated data —
 * the UI labels it clearly and it must never be treated as real votes,
 * real QR tokens or real results.
 *
 * The request/response shapes mirror the API contract documented in
 * README.md, so the same service files work unchanged against the real
 * Django backend.
 */
import { API_PATHS, delay } from "./apiPaths";

export const DEMO_CREDENTIALS = {
  admin: { identifier: "admin@securevote.org", password: "Admin@123", otp: "246810" },
  voter: { identifier: "voter@securevote.org", password: "Voter@123" },
  voter2: { identifier: "voter2@securevote.org", password: "Voter@123" },
};

/* ---------- tiny helpers ---------- */
const iso = (d) => d.toISOString();
const daysFromNow = (days, hours = 9) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  d.setHours(hours, 0, 0, 0);
  return d;
};
const rand = (n) => Math.floor(Math.random() * n).toString(36).padStart(Math.ceil(n.toString(36).length), "x");
const clone = (o) => JSON.parse(JSON.stringify(o));

/* ---------- seeded demo data ---------- */
const db = {
  users: [
    { id: 1, name: "A. Sterling", email: "admin@securevote.org", password: "Admin@123", role: "admin", voter_id: null },
    { id: 2, name: "Jordan Avery", email: "voter@securevote.org", password: "Voter@123", role: "voter", voter_id: "EV-1001" },
    { id: 3, name: "Riley Chen", email: "voter2@securevote.org", password: "Voter@123", role: "voter", voter_id: "EV-1002" },
  ],
  sessions: {}, // token -> userId
  otpPending: {}, // token -> { userId, code, expires }

  elections: [
    {
      id: 1,
      title: "Board of Directors Election 2026",
      description: "Election of four members of the Board of Directors for the 2026–2029 term. Open to all eligible corporate voters.",
      starts_at: iso(daysFromNow(-2)),
      ends_at: iso(daysFromNow(5, 23)),
      status: "active",
      results_published: false,
      results_verified: false,
      created_at: iso(daysFromNow(-10)),
    },
    {
      id: 2,
      title: "Annual General Meeting — Appointment of External Auditor",
      description: "Vote on the appointment of the external audit firm for the 2026 financial year.",
      starts_at: iso(daysFromNow(-1)),
      ends_at: iso(daysFromNow(3, 23)),
      status: "active",
      results_published: false,
      results_verified: false,
      created_at: iso(daysFromNow(-8)),
    },
    {
      id: 3,
      title: "Staff Council Election 2025",
      description: "Annual election of the Staff Council representatives for 2025–2026.",
      starts_at: iso(daysFromNow(-45)),
      ends_at: iso(daysFromNow(-30)),
      status: "closed",
      results_published: true,
      results_verified: true,
      published_at: iso(daysFromNow(-29)),
      created_at: iso(daysFromNow(-60)),
    },
    {
      id: 4,
      title: "Office Relocation Referendum",
      description: "Referendum on the proposed relocation of the headquarters to the North Campus.",
      starts_at: iso(daysFromNow(12)),
      ends_at: iso(daysFromNow(20)),
      status: "upcoming",
      results_published: false,
      results_verified: false,
      created_at: iso(daysFromNow(-4)),
    },
  ],

  candidates: [
    { id: 1, election_id: 1, name: "Amara Okafor", role: "Director nominee", description: "Chief Operations Officer with 15 years in enterprise logistics and compliance.", photo: null },
    { id: 2, election_id: 1, name: "Daniel Whitfield", role: "Director nominee", description: "Finance lead focused on long-term capital planning and risk governance.", photo: null },
    { id: 3, election_id: 1, name: "Priya Raman", role: "Director nominee", description: "Technology strategist; previously led digital transformation across three continents.", photo: null },
    { id: 4, election_id: 1, name: "Marcus Chen", role: "Director nominee", description: "People and culture specialist with deep experience in large-scale organisational change.", photo: null },
    { id: 5, election_id: 2, name: "Harrow & Grant LLP", role: "Audit firm candidate", description: "Big-4 firm with a dedicated sector practice and 12 years of tenure history.", photo: null },
    { id: 6, election_id: 2, name: "Meridian Audit Group", role: "Audit firm candidate", description: "Independent mid-size firm specialising in mid-market corporates.", photo: null },
    { id: 7, election_id: 2, name: "Kestrel & Co.", role: "Audit firm candidate", description: "Boutique firm offering technology-first assurance services.", photo: null },
    { id: 8, election_id: 3, name: "Sofia Marino", role: "Council candidate", description: "Representing the operations wing; chair of the safety working group.", photo: null },
    { id: 9, election_id: 3, name: "Tomasz Kowalski", role: "Council candidate", description: "Engineering representative; lead of the remote-work charter.", photo: null },
    { id: 10, election_id: 3, name: "Leila Haddad", role: "Council candidate", description: "HR partner focused on training, inclusion and benefits.", photo: null },
    { id: 11, election_id: 3, name: "Ben Osei", role: "Council candidate", description: "Facilities and sustainability advocate; energy-audit committee member.", photo: null },
  ],

  voters: [
    { id: 2, voter_id: "EV-1001", name: "Jordan Avery", email: "voter@securevote.org", department: "Operations", is_eligible: true },
    { id: 3, voter_id: "EV-1002", name: "Riley Chen", email: "voter2@securevote.org", department: "Engineering", is_eligible: true },
    { id: 10, voter_id: "EV-1003", name: "Miguel Santos", email: "m.santos@securevote.org", department: "Finance", is_eligible: true },
    { id: 11, voter_id: "EV-1004", name: "Hannah Novak", email: "h.novak@securevote.org", department: "Legal", is_eligible: true },
    { id: 12, voter_id: "EV-1005", name: "Aisha Bello", email: "a.bello@securevote.org", department: "Marketing", is_eligible: true },
    { id: 13, voter_id: "EV-1006", name: "Peter Lindqvist", email: "p.lindqvist@securevote.org", department: "IT", is_eligible: false },
    { id: 14, voter_id: "EV-1007", name: "Grace Osei", email: "g.osei@securevote.org", department: "HR", is_eligible: true },
    { id: 15, voter_id: "EV-1008", name: "Yusuf Demir", email: "y.demir@securevote.org", department: "Procurement", is_eligible: true },
  ],

  // Simulated ballots: electionId -> Set of voterIds (only "did they vote" is tracked,
  // never which candidate — mirroring the anonymity requirement).
  ballots: {
    1: new Set([11, 12, 15]),
    2: new Set([11]),
    3: new Set([2, 3, 10, 11, 12, 14, 15]),
  },
  // Pre-sealed counts for the closed & published election (demo only).
  sealedResults: {
    3: { "8": 132, "9": 87, "10": 96, "11": 64 },
  },

  qrTokens: {}, // token -> { election_id, voter_id, status, created_at, expires_at }
  audit: [
    { id: 901, at: iso(daysFromNow(-29)), actor: "A. Sterling (admin)", action: "RESULTS_PUBLISHED", detail: "Results of “Staff Council Election 2025” verified and published. Seal: 9F2C…D41A.", category: "results", status: "ok" },
    { id: 902, at: iso(daysFromNow(-30)), actor: "System", action: "ELECTION_CLOSED", detail: "“Staff Council Election 2025” closed at 23:59. Ballot intake sealed.", category: "election", status: "ok" },
    { id: 903, at: iso(daysFromNow(-1)), actor: "A. Sterling (admin)", action: "QR_ISSUED", detail: "Access token issued for “AGM — Appointment of External Auditor”.", category: "qr", status: "ok" },
    { id: 904, at: iso(daysFromNow(-1)), actor: "Riley Chen (voter EV-1002)", action: "VOTE_SUBMITTED", detail: "Ballot recorded for “AGM — Appointment of External Auditor”. Ref: R-7K2Q…", category: "vote", status: "ok" },
    { id: 905, at: iso(daysFromNow(-2)), actor: "A. Sterling (admin)", action: "ELECTION_CREATED", detail: "“Board of Directors Election 2026” opened for voting.", category: "election", status: "ok" },
  ],

  seq: { candidate: 20, audit: 1000, election: 10 },
  // Demo-only election eligibility records. Real eligibility is stored by Django.
  eligibility: [],
};

// Seed demo eligibility for active/upcoming elections and active voter accounts.
for (const election of db.elections.filter((e) => e.status !== "closed")) {
  for (const voter of db.voters.filter((v) => v.is_eligible)) {
    db.eligibility.push({ id: `${election.id}-${voter.id}`, election_id: election.id, voter_id: voter.id, is_eligible: true });
  }
}

/* seed one used token + pre-seed a vote so states are demo-able */
db.qrTokens["DEMO-USED-TOKEN"] = { election_id: 1, voter_id: 3, status: "used", created_at: iso(daysFromNow(-1)), expires_at: iso(daysFromNow(0, 23)) };

const ok = (data) => ({ data, status: 200 });
const fail = (status, error) => ({ data: null, status, error });

/* ---------- auth helpers ---------- */
function issueToken(userId) {
  const t = "demo-" + rand(1e9) + rand(1e9);
  db.sessions[t] = userId;
  return t;
}
function userFrom(token) {
  const uid = db.sessions[token];
  if (!uid) return null;
  const u = db.users.find((x) => x.id === uid);
  return u ? { id: u.id, name: u.name, email: u.email, role: u.role, voter_id: u.voter_id } : null;
}
function requireUser(token) {
  const u = userFrom(token);
  if (!u) return { err: fail(401, "Your session has expired. Please log in again.") };
  return { user: u };
}
function requireAdmin(token) {
  const r = requireUser(token);
  if (r.err) return r;
  if (r.user.role !== "admin") return { err: fail(403, "This operation requires administrator privileges.") };
  return r;
}
function pushAudit(action, detail, category, actor) {
  db.audit.unshift({ id: ++db.seq.audit, at: iso(new Date()), actor, action, detail, category, status: "ok" });
}
const hasVoted = (electionId, voterId) => !!db.ballots[electionId]?.has(voterId);

/* ---------- path router ---------- */
const p = API_PATHS;

/* Build an anchored regex for a path template whose trailing segment is an id. */
const idRoute = (tpl) => new RegExp(`^${String(tpl("__ID__")).replace(/\/+$/, "")}$`.replace("__ID__", "(\\d+)"));
const ROUTES = {
  electionDetail: idRoute(p.election),
  electionCandidates: idRoute(p.electionCandidates),
  candidateDetail: idRoute(p.candidate),
  vote: idRoute(p.vote),
  results: idRoute(p.results),
};
/* Accept FormData (photo uploads) or plain objects. */
const asObj = (b) => {
  if (typeof FormData !== "undefined" && b instanceof FormData) {
    const o = Object.fromEntries(b.entries());
    if (o.photo && o.photo !== "null") o.photo = typeof URL !== "undefined" && URL.createObjectURL ? URL.createObjectURL(o.photo) : null;
    return o;
  }
  return b || {};
};

export async function handle(method, path, body, token) {
  await delay(320 + Math.random() * 420); // simulated network latency

  const m = method.toLowerCase();
  const clean = (x) => String(x).replace(/\/+$/, "") || "/";
  const [rawPath, rawQuery = ""] = String(path).split("?");
  const query = Object.fromEntries(new URLSearchParams(rawQuery));
  const path0 = clean(rawPath);

  const route = (pattern) => clean(pattern) === path0;

  /* ================= AUTH ================= */
  if (m === "post" && route(p.login)) {
    const id = (body?.identifier || "").trim().toLowerCase();
    const u = db.users.find((x) => x.email.toLowerCase() === id || String(x.voter_id || "").toLowerCase() === id);
    if (!u || u.password !== body?.password) {
      return fail(401, "Invalid credentials. Check your email/voter ID and password.");
    }
    if (u.role === "admin") {
      // Demo: administrators get an OTP step. In a real deployment the OTP
      // is delivered by the backend (email/SMS) — never generated in the browser.
      const t = "otp-pending-" + rand(1e9);
      db.otpPending[t] = { userId: u.id, code: DEMO_CREDENTIALS.admin.otp, expires: Date.now() + 5 * 60 * 1000 };
      return ok({
        otp_required: true,
        otp_session: t,
        otp_channel: "email",
        demo_otp_code: DEMO_CREDENTIALS.admin.otp, // DEMO ONLY — never returned by a real backend
        message: "A one-time code was sent to your registered email address.",
      });
    }
    const t = issueToken(u.id);
    pushAudit("LOGIN", `${u.name} authenticated successfully.`, "auth", `${u.name} (${u.role})`);
    return ok({ otp_required: false, token: t, user: userFrom(t) });
  }

  if (m === "post" && route(p.otpVerify)) {
    const pend = db.otpPending[body?.otp_session || ""];
    if (!pend || pend.code !== String(body?.code || "").trim()) {
      return fail(400, "The one-time code is incorrect. Please try again.");
    }
    if (Date.now() > pend.expires) return fail(400, "The one-time code has expired. Log in again to receive a new one.");
    const t = issueToken(pend.userId);
    delete db.otpPending[body.otp_session];
    const u = userFrom(t);
    pushAudit("LOGIN", `${u.name} authenticated successfully (2FA).`, "auth", `${u.name} (${u.role})`);
    return ok({ token: t, user: u });
  }

  if (m === "get" && route(p.me)) {
    const r = requireUser(token);
    if (r.err) return r.err;
    return ok(r.user);
  }

  if (m === "post" && route(p.logout)) {
    const r = requireUser(token);
    if (r.err) return r.err;
    pushAudit("LOGOUT", `${r.user.name} signed out.`, "auth", `${r.user.name} (${r.user.role})`);
    delete db.sessions[token];
    return ok({ ok: true });
  }

  /* ================= ADMIN: stats ================= */
  if (m === "get" && route(p.adminStats)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const totalVotes = Object.values(db.ballots).reduce((a, s) => a + s.size, 0);
    return ok({
      elections_total: db.elections.length,
      elections_active: db.elections.filter((e) => e.status === "active").length,
      voters_total: db.voters.length,
      candidates_total: db.candidates.length,
      votes_total: totalVotes,
    });
  }

  /* ================= ADMIN: elections ================= */
  if (m === "get" && route(p.elections)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    return ok(db.elections.map((e) => ({ ...e, candidates_count: db.candidates.filter((c) => c.election_id === e.id).length, votes_cast: db.ballots[e.id]?.size || 0 })));
  }

  let match;
  if ((m === "get" || m === "patch" || m === "delete") && (match = path0.match(ROUTES.electionDetail))) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const e = db.elections.find((x) => x.id === Number(match[1]));
    if (!e) return fail(404, "Election not found.");
    if (m === "get") return ok({ ...e, candidates: db.candidates.filter((c) => c.election_id === e.id), votes_cast: db.ballots[e.id]?.size || 0 });
    if (m === "patch") {
      Object.assign(e, pick(body, ["title", "description", "starts_at", "ends_at", "status"]));
      pushAudit("ELECTION_UPDATED", `Election “${e.title}” was updated.`, "election", `${r.user.name} (admin)`);
      return ok(e);
    }
    db.elections = db.elections.filter((x) => x.id !== e.id);
    pushAudit("ELECTION_DELETED", `Election “${e.title}” was deleted.`, "election", `${r.user.name} (admin)`);
    return ok({ ok: true });
  }
  if (m === "post" && route(p.elections)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    if (!body?.title?.trim()) return fail(400, "Election title is required.");
    const e = {
      id: ++db.seq.election,
      title: body.title.trim(),
      description: body.description || "",
      starts_at: body.starts_at || iso(daysFromNow(1)),
      ends_at: body.ends_at || iso(daysFromNow(7)),
      status: body.status || "draft",
      results_published: false,
      results_verified: false,
      created_at: iso(new Date()),
    };
    db.elections.push(e);
    pushAudit("ELECTION_CREATED", `Election “${e.title}” was created.`, "election", `${r.user.name} (admin)`);
    return ok(e);
  }

  // Election publish/close actions mirror the Django action routes.
  const lifecycleMatch = path0.match(/^\/api\/elections\/(\d+)\/(publish|close)$/);
  if (m === "post" && lifecycleMatch) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const e = db.elections.find((x) => x.id === Number(lifecycleMatch[1]));
    if (!e) return fail(404, "Election not found.");
    if (lifecycleMatch[2] === "publish") {
      if (e.status !== "draft") return fail(409, "Election is not in draft state.");
      const eligible = db.eligibility.filter((x) => x.election_id === e.id && x.is_eligible);
      const tokens = Object.values(db.qrTokens).filter((x) => x.election_id === e.id && x.status === "valid");
      if (db.candidates.filter((x) => x.election_id === e.id).length < 2) return fail(400, "Add at least 2 candidates before publishing.");
      if (!eligible.length) return fail(400, "Add eligible voters before publishing.");
      if (tokens.length < eligible.length) return fail(400, "Generate QR tokens for all eligible voters before publishing.");
      e.status = "active";
      pushAudit("ELECTION_PUBLISHED", `Election “${e.title}” was published.`, "election", `${r.user.name} (admin)`);
    } else {
      if (e.status !== "active") return fail(409, "Only published elections can be closed.");
      e.status = "closed";
      pushAudit("ELECTION_CLOSED", `Election “${e.title}” was closed.`, "election", `${r.user.name} (admin)`);
    }
    return ok(e);
  }

  // Election-specific eligible voter list and assignment.
  const eligibilityMatch = path0.match(/^\/api\/elections\/(\d+)\/eligible-voters$/);
  if (eligibilityMatch && (m === "get" || m === "post")) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const electionId = Number(eligibilityMatch[1]);
    const election = db.elections.find((x) => x.id === electionId);
    if (!election) return fail(404, "Election not found.");
    if (m === "get") {
      return ok(db.eligibility.filter((x) => x.election_id === electionId).map((x) => {
        const voter = db.voters.find((v) => v.id === x.voter_id);
        return { id: x.id, is_eligible: x.is_eligible, has_voted: hasVoted(electionId, x.voter_id), voter: voter ? { id: voter.id, voter_code: voter.voter_id, full_name: voter.name, email: voter.email, department: voter.department, is_active: voter.is_eligible } : null };
      }));
    }
    if (election.status !== "draft") return fail(400, "Eligible voters can only be changed while the election is in draft.");
    const ids = Array.isArray(body?.voter_ids) ? body.voter_ids.map(Number) : [];
    if (!ids.length || ids.some((id) => !Number.isInteger(id))) return fail(400, "Select at least one valid voter.");
    let added = 0;
    for (const id of ids) {
      const voter = db.voters.find((v) => v.id === id && v.is_eligible);
      if (!voter) continue;
      if (!db.eligibility.some((x) => x.election_id === electionId && x.voter_id === id)) {
        db.eligibility.push({ id: `${electionId}-${id}`, election_id: electionId, voter_id: id, is_eligible: true });
        added += 1;
      }
    }
    pushAudit("ELIGIBLE_VOTERS_ADDED", `${added} eligible voter assignment(s) added to “${election.title}”.`, "voter", `${r.user.name} (admin)`);
    return ok({ added });
  }

  /* ================= ADMIN: candidates ================= */
  if (m === "get" && route(p.candidates)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const list = db.candidates.filter((c) => !body?.election_id || c.election_id === Number(body.election_id));
    return ok(list);
  }
  if (m === "get" && (match = path0.match(ROUTES.electionCandidates))) {
    // Ballot display data: any authenticated user may list candidates of an
    // election (admins also use this route for management).
    const r = requireUser(token);
    if (r.err) return r.err;
    const e = db.elections.find((x) => x.id === Number(match[1]));
    if (!e || e.status === "draft") return fail(404, "Election not found.");
    return ok(db.candidates.filter((c) => c.election_id === e.id));
  }
  if (m === "post" && route(p.candidates)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const data0 = asObj(body);
    if (!data0?.name?.trim()) return fail(400, "Candidate name is required.");
    const c = { id: ++db.seq.candidate, election_id: Number(data0.election_id ?? data0.election), name: data0.name.trim(), role: data0.role || "", description: data0.description || "", photo: data0.photo || data0.photo_url || null };
    db.candidates.push(c);
    pushAudit("CANDIDATE_ADDED", `Candidate “${c.name}” added.`, "candidate", `${r.user.name} (admin)`);
    return ok(c);
  }
  if ((m === "patch" || m === "delete") && (match = path0.match(ROUTES.candidateDetail))) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const c = db.candidates.find((x) => x.id === Number(match[1]));
    if (!c) return fail(404, "Candidate not found.");
    if (m === "patch") {
      const data0 = asObj(body);
      const next = pick(data0, ["name", "role", "description", "election_id", "photo_url"]);
      if (data0.election && !data0.election_id) next.election_id = Number(data0.election);
      if (data0.photo) next.photo = data0.photo;
      Object.assign(c, next);
      pushAudit("CANDIDATE_UPDATED", `Candidate “${c.name}” was updated.`, "candidate", `${r.user.name} (admin)`);
      return ok(c);
    }
    db.candidates = db.candidates.filter((x) => x.id !== c.id);
    pushAudit("CANDIDATE_REMOVED", `Candidate “${c.name}” was removed.`, "candidate", `${r.user.name} (admin)`);
    return ok({ ok: true });
  }

  /* ================= ADMIN: voters ================= */
  if (m === "get" && route(p.voters)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const q = (query.search || body?.search || "").toLowerCase();
    let list = db.voters.map((v) => ({ ...v, has_voted_elections: Object.entries(db.ballots).filter(([eid, set]) => set.has(v.id)).map(([eid]) => db.elections.find((e) => e.id === Number(eid))?.title).filter(Boolean) }));
    if (q) list = list.filter((v) => [v.name, v.voter_id, v.email, v.department].join(" ").toLowerCase().includes(q));
    // Never expose which candidate a voter chose — only the fact that they voted.
    return ok(list);
  }
  if (m === "post" && route(p.voters)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    if (!body?.name?.trim() || !body?.voter_id?.trim()) return fail(400, "Voter ID and full name are required.");
    if (db.voters.some((v) => v.voter_id === body.voter_id.trim())) return fail(409, "A voter with this voter ID already exists.");
    const v = { id: 100 + db.voters.length + 1, voter_id: body.voter_id.trim(), name: body.name.trim(), email: body.email || "", department: body.department || "—", is_eligible: body.is_eligible !== false };
    db.voters.push(v);
    pushAudit("VOTER_REGISTERED", `Voter ${v.voter_id} registered.`, "voter", `${r.user.name} (admin)`);
    return ok(v);
  }

  /* ================= QR ================= */
  const qrGenerateMatch = path0.match(/^\/api\/elections\/(\d+)\/generate-qr$/);
  if (m === "post" && qrGenerateMatch) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const electionId = Number(qrGenerateMatch[1]);
    const e = db.elections.find((x) => x.id === electionId);
    if (!e) return fail(404, "Election not found.");
    if (e.status !== "draft") return fail(400, "QR tokens can only be generated before publishing.");
    const eligible = db.eligibility.filter((x) => x.election_id === electionId && x.is_eligible);
    let createdCount = 0;
    for (const row of eligible) {
      const existing = Object.values(db.qrTokens).some((x) => x.election_id === electionId && x.voter_id === row.voter_id && x.status === "valid");
      if (existing) continue;
      const tokenStr = `EVQR-DEMO-${rand(1e7).toUpperCase()}-${rand(1e4).toUpperCase()}`;
      const created = new Date();
      const expires = new Date(created.getTime() + 30 * 60 * 1000);
      db.qrTokens[tokenStr] = {
        election_id: electionId, voter_id: row.voter_id, status: "valid",
        created_at: iso(created), expires_at: iso(expires),
        qr_payload: `${(import.meta.env?.VITE_API_BASE_URL || "https://vote.example.org")}/api/qr/verify/?token=${tokenStr}&election=${electionId}`,
      };
      createdCount += 1;
    }
    pushAudit("QR_TOKENS_GENERATED", `${createdCount} QR token(s) generated for “${e.title}”.`, "qr", `${r.user.name} (admin)`);
    const total = Object.values(db.qrTokens).filter((x) => x.election_id === electionId).length;
    return ok({ created: createdCount, total, demo: true });
  }

  const qrDownloadMatch = path0.match(/^\/api\/elections\/(\d+)\/voters\/(\d+)\/qr$/);
  if (m === "get" && qrDownloadMatch) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const electionId = Number(qrDownloadMatch[1]);
    const voterId = Number(qrDownloadMatch[2]);
    const qr = Object.values(db.qrTokens).find((x) => x.election_id === electionId && x.voter_id === voterId && x.status === "valid");
    if (!qr) return fail(404, "No valid QR token exists for this voter and election. Generate tokens first.");
    return ok({ qr_payload: qr.qr_payload });
  }

  if (m === "post" && route(p.qrVerify)) {
    const raw = String(body?.token || "").trim().toUpperCase();
    if (!raw) return fail(400, "Please provide an access token.");
    // Demo test tokens so every verification state can be previewed:
    if (raw === "DEMO-VALID-TOKEN") {
      const e = db.elections.find((x) => x.id === Number(body?.election_id)) || db.elections.find((x) => x.status === "active");
      if (!e) return fail(404, "Election not found.");
      const created = new Date();
      db.qrTokens[raw] = { election_id: e.id, voter_id: null, status: "valid", created_at: iso(created), expires_at: iso(new Date(created.getTime() + 30 * 60 * 1000)), qr_payload: "demo-valid" };
    }
    if (raw === "DEMO-EXPIRED-TOKEN") return ok({ valid: false, reason: "expired", message: "This access token has expired. Please request a new one." });
    if (raw === "DEMO-USED-TOKEN") return ok({ valid: false, reason: "used", message: "This access token has already been used. Each token can be used only once." });

    const t = db.qrTokens[raw];
    if (!t) {
      pushAudit("QR_REJECTED", "Unknown access token was rejected.", "qr", "System");
      return ok({ valid: false, reason: "invalid", message: "This access token is not recognised. Check it and try again." });
    }
    const e = db.elections.find((x) => x.id === t.election_id);
    if (new Date(t.expires_at) < new Date()) {
      t.status = "expired";
      return ok({ valid: false, reason: "expired", message: "This access token has expired. Please request a new one." });
    }
    if (t.status === "used") {
      return ok({ valid: false, reason: "used", message: "This access token has already been used. Each token can be used only once." });
    }
    // Bind the token to the authenticated voter (the QR is access proof, not identity).
    const r = requireUser(token);
    if (r.err) return r.err;
    const voter = db.voters.find((v) => v.voter_id === r.user.voter_id);
    const eligible = voter && db.eligibility.some((x) => x.election_id === e.id && x.voter_id === voter.id && x.is_eligible);
    if (!voter || !voter.is_eligible || !eligible) {
      return ok({ valid: false, reason: "not_eligible", message: "Your voter record is not eligible for this election. Contact your election administrator." });
    }
    if (e.status !== "active") {
      return ok({ valid: false, reason: "election_not_active", message: `This election is ${e.status} and is not accepting votes.` });
    }
    if (t.voter_id && t.voter_id !== voter.id) {
      return ok({ valid: false, reason: "not_eligible", message: "This QR token was issued to another voter." });
    }
    if (hasVoted(e.id, voter.id)) {
      t.status = "used";
      return ok({ valid: false, reason: "already_voted", message: "You have already voted in this election. Duplicate ballots are not permitted." });
    }
    t.voter_id = voter.id;
    return ok({ valid: true, reason: "ok", election_id: e.id, election_title: e.title, voter_id: voter.voter_id, verification_token: raw, has_voted: false });
  }

  /* ================= VOTER: elections ================= */
  if (m === "get" && route(p.voterElections)) {
    const r = requireUser(token);
    if (r.err) return r.err;
    if (r.user.role !== "voter") return fail(403, "Voter account required.");
    const voter = db.voters.find((v) => v.voter_id === r.user.voter_id);
    return ok(
      db.elections
        .filter((e) => e.status !== "draft" && db.eligibility.some((x) => x.election_id === e.id && x.voter_id === voter?.id && x.is_eligible))
        .map((e) => ({
          id: e.id,
          title: e.title,
          description: e.description,
          starts_at: e.starts_at,
          ends_at: e.ends_at,
          status: e.status,
          eligible: !!voter?.is_eligible && db.eligibility.some((x) => x.election_id === e.id && x.voter_id === voter?.id && x.is_eligible),
          has_voted: hasVoted(e.id, voter?.id),
          candidates_count: db.candidates.filter((c) => c.election_id === e.id).length,
        }))
    );
  }

  /* ================= VOTING (matched before the generic election route) ================= */
  if (m === "post" && (match = path0.match(ROUTES.vote))) {
    const r = requireUser(token);
    if (r.err) return r.err;
    if (r.user.role !== "voter") return fail(403, "Only registered voters may cast ballots.");
    const e = db.elections.find((x) => x.id === Number(match[1]));
    if (!e) return fail(404, "Election not found.");
    if (e.status !== "active") return fail(409, "This election is not currently accepting votes.");
    const voter = db.voters.find((v) => v.voter_id === r.user.voter_id);
    if (!voter?.is_eligible || !db.eligibility.some((x) => x.election_id === e.id && x.voter_id === voter.id && x.is_eligible)) return fail(403, "Your voter record is not eligible for this election.");
    if (hasVoted(e.id, voter.id)) return fail(409, "You have already voted in this election. Duplicate ballots are not permitted.");
    const vt = db.qrTokens[body?.verification_token];
    if (!vt || vt.status !== "valid" || vt.election_id !== e.id) return fail(400, "The QR verification token is missing or invalid. Please re-scan to enter the ballot.");
    if (vt.voter_id !== voter.id) return fail(403, "This access token was issued to another voter.");
    const cand = db.candidates.find((c) => c.id === Number(body?.candidate_id) && c.election_id === e.id);
    if (!cand) return fail(400, "Selected candidate is not part of this election.");
    // "Count" the ballot (candidate choice stays sealed inside the backend).
    db.sealedResults[e.id] = { ...(db.sealedResults[e.id] || {}), [String(cand.id)]: (db.sealedResults[e.id]?.[String(cand.id)] || 0) + 1 };
    (db.ballots[e.id] ||= new Set()).add(voter.id);
    vt.status = "used";
    const ref = "R-" + rand(1e5).toUpperCase() + "-" + rand(1e5).toUpperCase();
    pushAudit("VOTE_SUBMITTED", `Ballot recorded for “${e.title}”. Ref: ${ref.slice(0, 8)}… (candidate hidden)`, "vote", `${voter.name} (${voter.voter_id})`);
    return ok({ success: true, reference_id: ref });
  }

  /* ================= RESULTS & AUDIT (admin) ================= */
  if ((match = path0.match(ROUTES.results))) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    const e = db.elections.find((x) => x.id === Number(match[1]));
    if (!e) return fail(404, "Election not found.");
    if (!e.results_published || !e.results_verified) {
      return ok({
        election_id: e.id,
        election_title: e.title,
        status: e.status,
        results_published: e.results_published,
        results_verified: e.results_verified,
        total_votes: null,
        candidates: [],
        audit_verified: e.results_verified,
        audit_summary: e.status === "closed" ? "The election is closed. Results are being sealed and verified by the audit trail. Official figures will appear here once verification completes." : "Results become available after the election closes and the audit trail is verified.",
      });
    }
    const cands = db.candidates.filter((c) => c.election_id === e.id);
    const counts = db.sealedResults[e.id] || {};
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    return ok({
      election_id: e.id,
      election_title: e.title,
      status: e.status,
      results_published: true,
      results_verified: true,
      published_at: e.published_at,
      total_votes: total,
      audit_verified: true,
      audit_summary: "All ballots in this election were validated against the QR access tokens and recorded in the append-only audit trail. The hash chain has been verified and no tampering indicators were found.",
      candidates: cands.map((c) => {
        const votes = counts[String(c.id)] || 0;
        return { id: c.id, name: c.name, role: c.role, votes, percentage: total ? Math.round((votes / total) * 1000) / 10 : 0 };
      }),
    });
  }

  if (m === "get" && route(p.auditLogs)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    return ok(db.audit);
  }
  if (m === "get" && route(p.auditVerify)) {
    const r = requireAdmin(token);
    if (r.err) return r.err;
    return ok({ intact: true, first_bad_record_id: null });
  }

  return fail(404, `No handler for ${method} ${path} in demo mode.`);
}

function pick(obj, keys) {
  const out = {};
  for (const k of keys) if (obj[k] !== undefined) out[k] = obj[k];
  return out;
}
