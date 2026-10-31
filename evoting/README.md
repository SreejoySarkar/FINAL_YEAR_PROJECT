# Secure E-Voting System – Person 2 modules

Django + DRF + PostgreSQL. LSAG ring signatures (anonymous authorisation), Paillier (encrypted votes),
Fiat–Shamir NIZK (ballot validity), hash-chained audit log, homomorphic tally.
Person 1's voters / elections / candidates are **referenced, never re-created** (see "Integrating Person 1").

## 1. Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit secrets + DB credentials
createdb evoting                # or use Person 1's database
python manage.py makemigrations # generates migrations for all apps (see note below)
python manage.py migrate
python manage.py seed_demo --voters 5     # demo election + pre-built ballots (stub tables only)
python manage.py runserver
```

Tests: `pytest` (uses SQLite in memory + 512-bit Paillier – tests only).
Performance: `locust -f tests/performance/locustfile.py --host http://127.0.0.1:8000`.

> **Folder rename:** the scope called the crypto folder `cryptography/`. That name shadows the PyPI
> package `cryptography` (needed for Fernet key encryption), so it is `evoting_crypto/` here.
> `apps/common/` (shared errors, throttles, the Person-1 adapter) and `apps/p1_stub/` (local stand-in
> tables, disabled with `USE_P1_STUB=False`) are the only additions to the planned structure.
> Per-app tests live in `tests/` rather than inside every app.

## 2. Structure

```
manage.py  pytest.ini  requirements.txt  .env.example
config/            settings.py  settings_test.py  urls.py  asgi.py  wsgi.py
evoting_crypto/    hashing.py  paillier.py  lsag.py  nizk.py  key_management.py
apps/
  common/                  ApiError, throttles, PublicAPIView, integration.py (ONLY file touching Person 1's models)
  p1_stub/                 dev-only Voter/Election/Candidate + `seed_demo`
  qr_validation/           QRToken            -> table qr_token
  voter_authorization/     VoterEligibility   -> table voter_eligibility
  anonymous_authorization/ AuthorizationCredential -> authorization_credential (no voter column)
  duplicate_voting/        LSAG verify + key-image uniqueness (service + check endpoint)
  ballot_management/       ballot definition, proof context, signed message format
  vote_encryption/         ElectionKey        -> election_key   (+ create_election_key command)
  nizk_proofs/             prove/verify wrappers + public verify endpoint
  vote_submission/         /votes/submit/, ballot_builder.py (client logic), demo endpoint
  anonymous_storage/       AnonymousBallot, EncryptedVoteComponent -> anonymous_ballot, encrypted_vote_component
  authorization_management/ admin summary, credential list/revoke
  audit_management/        AuditLog           -> audit_log (append-only hash chain)
  election_verification/   re-verifies every ballot; public auditor data
  result_calculation/      ElectionResult     -> election_result; homomorphic tally
  result_publication/      publish + public result
  ai_assistance/           statistical anomaly detection over audit metadata
tests/  tools/voter_client.py  postman/evoting.postman_collection.json
```

## 3. The voting protocol as implemented

| Phase (Person 1 `status`) | Step |
|---|---|
| `upcoming` (registration) | Admin syncs eligibility → creates Paillier key → generates **signed, expiring QR** per voter. |
| `upcoming` | Voter scans QR, generates an LSAG key pair **locally**, sends `token + public_key + proof-of-possession`. Server checks signature, expiry, DB state, eligibility; consumes the token; stores the public key as an `authorization_credential` **with no voter reference**. |
| `ongoing` (voting) | Ring = all ACTIVE public keys (frozen – no new registrations). Voter encrypts a one-hot vector with Paillier, proves it is valid (NIZK), ring-signs the ciphertexts with LSAG, submits. **No login, no voter ID.** |
| | Server: NIZK check → LSAG check → key-image duplicate check → atomic insert. `UNIQUE(election_id, key_image)` makes simultaneous double votes impossible (one gets `409 DUPLICATE_VOTE`). |
| `closed` | Admin runs verification, then tally: ciphertexts are multiplied per candidate, **only the aggregates are decrypted**, totals must equal the number of valid ballots. Admin publishes. |

### Cryptographic design notes
* **LSAG** (secp256k1, pure Python). Key image `I = x·H(election_id)` → same voter + same election = same image (linkable); different elections are unlinkable. The signed message is the ciphertext set, so an authorisation can't be reused for another ballot.
* **Proof of possession** at registration (Schnorr) blocks rogue-key attacks on the ring.
* **Paillier** `g = n+1`, 2048-bit by default. Private key = `p, q` encrypted with Fernet (scrypt-derived key) in `KEY_STORE_DIR`, never in PostgreSQL.
* **NIZK**: per-option OR-proof "encrypts 0 or 1" + sum-proof "product encrypts 1", Fiat–Shamir with 128-bit challenges. The challenge hash includes election, ballot definition **and the key image**, so a proof cannot be copied into another voter's ballot.
* **Audit log**: `event_hash = SHA256(previous_hash ‖ actor ‖ election ‖ action ‖ details ‖ time)`, written under a PostgreSQL advisory lock; `GET /api/audit/verify-chain/` detects edits/deletions.
* Ballot ids are random UUIDs and timestamps are truncated to the minute, so storage order doesn't reveal who voted when.

## 4. API reference

Admin endpoints use Django admin users (Basic auth in Postman; **HTTPS only** in production – swap to Person 1's auth in `REST_FRAMEWORK`). Everything is **deny-by-default**; public views opt in via `PublicAPIView` and are IP-throttled.

| Method & path | Who | Purpose |
|---|---|---|
| POST `/api/voter-authorization/sync/` | admin | create eligibility rows from Person 1's active voters |
| GET/PATCH `/api/voter-authorization/eligibility/` | admin | list / toggle eligibility |
| POST `/api/encryption/election-keys/` | admin | generate Paillier key (public part in DB) |
| GET `/api/encryption/election-keys/<id>/public/` | public | election public key |
| POST `/api/qr/generate/` | admin | signed QR token + PNG (base64) for one voter |
| POST `/api/qr/validate/` | public | check a token without consuming it |
| POST `/api/anonymous-auth/credentials/` | public (QR) | register anonymous public key |
| GET `/api/anonymous-auth/ring/<id>/` | public | ring keys + hash |
| GET `/api/ballots/<id>/` | public | candidates (option indexes), definition hash, public key |
| POST `/api/votes/submit/` | public | submit encrypted, proven, ring-signed ballot |
| GET `/api/duplicate/check/` | public | has this key image voted? |
| POST `/api/nizk/verify/` | public | verify a ballot proof |
| POST `/api/verification/<id>/run/` | admin | re-verify all ballots + audit chain |
| GET `/api/verification/<id>/public-data/` | public | all public ballot data for independent audit |
| POST `/api/result-calculation/<id>/calculate/` | admin | homomorphic tally (election closed) |
| POST `/api/results/<id>/publish/` · GET `/api/results/<id>/` | admin · public | publish / read results |
| GET `/api/authorization/<id>/summary/` | admin | counts; POST `.../credentials/<ref>/revoke/` (registration only) |
| GET `/api/audit/logs/` · `/api/audit/verify-chain/` | admin | audit trail |
| GET `/api/ai/anomalies/<id>/` | admin | anomaly report |
| POST `/api/anonymous-auth/dev/keypair/`, `/api/votes/demo-cast/` | demo only | `ENABLE_DEMO_ENDPOINTS=True` – server sees keys/choices, **never in production** |

Errors always look like `{"code": "DUPLICATE_VOTE", "message": "..."}`. Common codes: `QR_INVALID` 400, `QR_EXPIRED` 410,
`QR_ALREADY_USED` 409, `NOT_ELIGIBLE` 403, `ELECTION_PHASE_INVALID` 409, `INVALID_PROOF` 422,
`INVALID_RING_SIGNATURE` 422, `DUPLICATE_VOTE` 409, `VOTING_CLOSED` 409, `KEY_ACCESS_DENIED` 403.

### Postman
Import `postman/evoting.postman_collection.json`, run `seed_demo`-free or with it:
1. Create an election (status `upcoming`) with ≥2 candidates and ≥3 voters in Person 1's data (or the stub admin), set `election_id`, `voter_id`.
2. Run requests 1→3 (sync, key, QR) → 5→6 (keypair + register) for **at least 3 voters** (`MIN_RING_SIZE`).
3. Set the election to `ongoing`; run 8 and 9 (`candidate_id` from step 8). Re-run 9 → expect `409 DUPLICATE_VOTE`.
4. Set `closed`; run 11, 13, 14, 15.
For realistic testing use `tools/voter_client.py`, which keeps keys and choices on the client.

## 5. Integrating Person 1
Confirm with Person 1: model paths, primary-key types, the election status values, the voter "active" column, and how candidates link to elections. Then only edit `.env` (`P1_*_MODEL`, `USE_P1_STUB=False`) and `P1_FIELDS` / `P1_STATUS_VALUES` in `settings.py`. Re-run `makemigrations` so foreign keys point at their tables. Candidate order must not change once voting starts (the ballot definition hash is checked on every submission and verification).

## 6. Hardening checklist / known limits (read before production)
* **Registration anonymity.** At registration the server briefly knows (voter, public key). It stores no link, but a malicious operator with network/DB-time access could correlate by timing. Mitigations: client-side key generation (default), registration windows with randomised delays, and log hygiene. Voting itself is unlinkable to the credential.
* **LSAG cost is O(ring size)** (~8 ms per ring member to verify in pure Python on a laptop). Measure with Locust; for large electorates use libsecp256k1, background verification, or bounded sub-rings.
* **Result decryption has no zero-knowledge proof of correct decryption**; auditors can recompute the aggregates from public data but must trust the key holder's decryption. Add threshold Paillier / a decryption proof for stronger guarantees. The passphrase should be split among officials; use an HSM/KMS for the key.
* Make `anonymous_ballot`, `encrypted_vote_component` and `audit_log` insert-only at the PostgreSQL level (`REVOKE UPDATE, DELETE ... FROM app_role`), and ship the audit `head_hash` to an external witness periodically.
* Use Redis for DRF throttling in multi-process deployments; terminate TLS; set `DJANGO_DEBUG=False` and real secrets (the app refuses to start without them).
* The admin who generates QR codes can obtain voter tokens; deliver codes through a trusted channel and keep admin actions audited (they are).
* This is project-grade code. Have the cryptography independently reviewed before a real election.
