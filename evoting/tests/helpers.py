from apps.anonymous_authorization.services import pop_context
from apps.vote_submission.ballot_builder import build_signed_ballot
from evoting_crypto import lsag


def prepare_election(admin, election):
    assert admin.post("/api/voter-authorization/sync/", {"election_id": election.pk}, format="json").status_code == 200
    r = admin.post("/api/encryption/election-keys/", {"election_id": election.pk}, format="json")
    assert r.status_code == 201, r.data


def get_qr_token(admin, election, voter):
    r = admin.post("/api/qr/generate/", {"voter_id": voter.pk, "election_id": election.pk}, format="json")
    assert r.status_code == 201, r.data
    return r.data["token"]


def register(anon, election, token, x=None):
    if x is None:
        x, y = lsag.generate_keypair()
    else:
        y = lsag.public_key_of(x)
    body = {"token": token, "public_key": y, "possession_proof": lsag.prove_possession(x, pop_context(election.pk))}
    return x, anon.post("/api/anonymous-auth/credentials/", body, format="json")


def set_status(election, status):
    election.status = status
    election.save()


def build_payload(anon, election, x, candidate):
    ballot = anon.get(f"/api/ballots/{election.pk}/").data
    ring = anon.get(f"/api/anonymous-auth/ring/{election.pk}/").data["public_keys"]
    return build_signed_ballot(
        election_id=election.pk, definition={"options": ballot["options"], "hash": ballot["definition_hash"]},
        paillier_public=ballot["encryption"]["public_key"], ring_hex=ring, private_key=x, candidate_id=str(candidate.pk))


def cast(anon, election, x, candidate):
    return anon.post("/api/votes/submit/", build_payload(anon, election, x, candidate), format="json")


def full_registration(admin, anon, election, voters):
    prepare_election(admin, election)
    keys = []
    for v in voters:
        x, r = register(anon, election, get_qr_token(admin, election, v))
        assert r.status_code == 201, r.data
        keys.append(x)
    return keys
