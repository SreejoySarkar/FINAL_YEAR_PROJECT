import copy

import pytest
from django.test import override_settings

from apps.audit_management.models import AuditLog
from apps.audit_management.services import verify_chain
from apps.p1_stub.models import Candidate, Voter
from apps.voter_authorization.models import VoterEligibility

from .helpers import build_payload, cast, full_registration, get_qr_token, prepare_election, register, set_status


def candidates(election):
    return list(Candidate.objects.filter(election=election).order_by("pk"))


@pytest.mark.django_db
def test_double_vote_is_rejected(admin_client, anon_client, election, voters):
    keys = full_registration(admin_client, anon_client, election, voters)
    set_status(election, "ongoing")
    a, b, _ = candidates(election)
    assert cast(anon_client, election, keys[0], a).status_code == 201
    second = cast(anon_client, election, keys[0], b)         # same voter, different choice, fresh signature
    assert second.status_code == 409 and second.data["code"] == "DUPLICATE_VOTE"
    assert anon_client.get(f"/api/duplicate/check/?election_id={election.pk}&key_image="
                           + build_payload(anon_client, election, keys[0], a)["ring_signature"]["key_image"]).data["used"]


@pytest.mark.django_db
def test_qr_token_is_single_use_and_tamper_proof(admin_client, anon_client, election, voters):
    prepare_election(admin_client, election)
    token = get_qr_token(admin_client, election, voters[0])
    assert anon_client.post("/api/qr/validate/", {"token": token}, format="json").data["valid"]
    _, ok = register(anon_client, election, token)
    assert ok.status_code == 201
    _, again = register(anon_client, election, token)
    assert again.status_code == 409 and again.data["code"] == "QR_ALREADY_USED"
    forged = anon_client.post("/api/qr/validate/", {"token": token[:-3] + "abc"}, format="json")
    assert forged.status_code == 400 and forged.data["code"] == "QR_INVALID"
    reissue = admin_client.post("/api/qr/generate/", {"voter_id": voters[0].pk, "election_id": election.pk}, format="json")
    assert reissue.status_code == 409 and reissue.data["code"] == "ALREADY_REGISTERED"


@pytest.mark.django_db
def test_expired_qr_token(admin_client, anon_client, election, voters):
    prepare_election(admin_client, election)
    token = get_qr_token(admin_client, election, voters[0])
    with override_settings(QR_TOKEN_TTL_SECONDS=-1):
        r = anon_client.post("/api/qr/validate/", {"token": token}, format="json")
    assert r.status_code == 410 and r.data["code"] == "QR_EXPIRED"


@pytest.mark.django_db
def test_ineligible_voter_cannot_get_qr(admin_client, election, voters):
    prepare_election(admin_client, election)
    VoterEligibility.objects.filter(voter=voters[0]).update(is_eligible=False)
    r = admin_client.post("/api/qr/generate/", {"voter_id": voters[0].pk, "election_id": election.pk}, format="json")
    assert r.status_code == 403 and r.data["code"] == "NOT_ELIGIBLE"
    inactive = Voter.objects.create(name="x", email="x@example.org", is_active=False)
    assert admin_client.post("/api/qr/generate/", {"voter_id": inactive.pk, "election_id": election.pk}, format="json").status_code in (403, 409)


@pytest.mark.django_db
def test_voting_only_while_open(admin_client, anon_client, election, voters):
    keys = full_registration(admin_client, anon_client, election, voters)
    a, *_ = candidates(election)
    payload = build_payload(anon_client, election, keys[0], a)
    assert anon_client.post("/api/votes/submit/", payload, format="json").data["code"] == "VOTING_CLOSED"
    set_status(election, "closed")
    assert anon_client.post("/api/votes/submit/", payload, format="json").status_code == 409


@pytest.mark.django_db
def test_tampered_ballot_and_outsider_rejected(admin_client, anon_client, election, voters):
    keys = full_registration(admin_client, anon_client, election, voters)
    set_status(election, "ongoing")
    a, b, _ = candidates(election)
    payload = build_payload(anon_client, election, keys[0], a)
    swapped = copy.deepcopy(payload)
    swapped["ciphertexts"][0], swapped["ciphertexts"][1] = swapped["ciphertexts"][1], swapped["ciphertexts"][0]
    r = anon_client.post("/api/votes/submit/", swapped, format="json")
    assert r.status_code == 422 and r.data["code"] == "INVALID_PROOF"
    bad_sig = copy.deepcopy(payload)
    bad_sig["ring_signature"]["c0"] = "1"
    assert anon_client.post("/api/votes/submit/", bad_sig, format="json").data["code"] == "INVALID_RING_SIGNATURE"
    assert AuditLog.objects.filter(action="VOTE_REJECTED").count() == 2


@pytest.mark.django_db
def test_admin_endpoints_require_admin(anon_client, election):
    assert anon_client.post("/api/qr/generate/", {"voter_id": 1, "election_id": election.pk}, format="json").status_code in (401, 403)
    assert anon_client.get("/api/audit/logs/").status_code in (401, 403)
    assert anon_client.post(f"/api/result-calculation/{election.pk}/calculate/").status_code in (401, 403)


@pytest.mark.django_db
def test_result_needs_closed_election_and_correct_passphrase(admin_client, anon_client, election, voters):
    keys = full_registration(admin_client, anon_client, election, voters)
    set_status(election, "ongoing")
    a, *_ = candidates(election)
    cast(anon_client, election, keys[0], a)
    assert admin_client.post(f"/api/result-calculation/{election.pk}/calculate/").data["code"] == "ELECTION_NOT_CLOSED"
    set_status(election, "closed")
    r = admin_client.post(f"/api/result-calculation/{election.pk}/calculate/", {"passphrase": "wrong"}, format="json")
    assert r.status_code == 403 and r.data["code"] == "KEY_ACCESS_DENIED"


@pytest.mark.django_db
def test_audit_chain_detects_tampering(admin_client, anon_client, election, voters):
    full_registration(admin_client, anon_client, election, voters[:2])
    assert verify_chain()["ok"]
    victim = AuditLog.objects.order_by("id")[1]
    AuditLog.objects.filter(pk=victim.pk).update(action="NOTHING_TO_SEE")   # bypasses the immutable save()
    result = verify_chain()
    assert not result["ok"] and result["first_broken_id"] == victim.pk
    with pytest.raises(PermissionError):
        AuditLog.objects.first().delete()
