import pytest

from apps.anonymous_storage.models import AnonymousBallot
from apps.audit_management.services import verify_chain
from apps.p1_stub.models import Candidate

from .helpers import cast, full_registration, set_status


@pytest.mark.django_db
def test_complete_election_end_to_end(admin_client, anon_client, election, voters):
    keys = full_registration(admin_client, anon_client, election, voters)
    set_status(election, "ongoing")
    alice, bob, _ = Candidate.objects.filter(election=election).order_by("pk")

    choices = [alice, bob, alice, alice]
    for x, candidate in zip(keys, choices):
        r = cast(anon_client, election, x, candidate)
        assert r.status_code == 201, r.data

    # anonymity of storage: the ballot table has no voter column
    assert "voter" not in {f.name for f in AnonymousBallot._meta.get_fields()}

    set_status(election, "closed")
    r = admin_client.post(f"/api/result-calculation/{election.pk}/calculate/", {}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["verification_status"] == "VERIFIED"
    votes = {c["label"]: c["votes"] for c in r.data["result_data"]["candidates"]}
    assert votes == {"Alice": 3, "Bob": 1, "Carol": 0}

    assert anon_client.get(f"/api/results/{election.pk}/").status_code == 404      # not published yet
    assert admin_client.post(f"/api/results/{election.pk}/publish/").status_code == 200
    public = anon_client.get(f"/api/results/{election.pk}/")
    assert public.status_code == 200 and public.data["valid_ballots"] == 4

    assert verify_chain()["ok"]
    report = admin_client.post(f"/api/verification/{election.pk}/run/").data
    assert report["passed"] and report["ballots_verified"] == 4
    assert admin_client.get(f"/api/ai/anomalies/{election.pk}/").status_code == 200
    assert admin_client.get(f"/api/authorization/{election.pk}/summary/").data["ballots_cast"] == 4
