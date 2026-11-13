
from rest_framework.test import APIClient

from accounts.models import Admin
from testkit import validate, vote
from voters.models import Eligibility, Voter
from voting.helpers import create_token_row


def test_full_flow_tally_and_publish(live_election):
    e = live_election["election"]
    c1, c2 = live_election["candidates"]
    people = [(live_election["voter"], live_election["token"])]

    for i in (2, 3):
        v = Voter.objects.create(
            voter_code=f"V00{i}",
            full_name=f"Voter {i}",
            email=f"v{i}@x.com"
        )
        Eligibility.objects.create(voter=v, election=e)
        people.append((v, create_token_row(e, v)[1]))

    for (v, token), cid in zip(people, [c1.id, c1.id, c2.id]):
        session = validate(token, v.voter_code).data["vote_session"]
        assert vote(session, cid).status_code == 201

    admin = APIClient()
    admin.force_authenticate(live_election["admin"])

    assert admin.post(
        f"/api/elections/{e.id}/finalize"
    ).status_code == 400  # still open

    e.status = "closed"
    e.save()

    r = admin.post(f"/api/elections/{e.id}/finalize")
    assert r.status_code == 200
    assert r.data["total_votes"] == 3
    assert r.data["winner_ids"] == [c1.id]

    assert APIClient().get(
        f"/api/elections/{e.id}/results"
    ).status_code == 403

    assert admin.post(
        f"/api/elections/{e.id}/publish-results"
    ).status_code == 200

    assert APIClient().get(
        f"/api/elections/{e.id}/results"
    ).status_code == 200


def test_unauthenticated_cannot_finalize(live_election):
    e = live_election["election"]
    assert APIClient().post(
        f"/api/elections/{e.id}/finalize"
    ).status_code == 401


def test_auditor_cannot_finalize(live_election):
    auditor = Admin.objects.create_user(
        username="au",
        email="au@x.com",
        password="Pass#12345",
        role="auditor"
    )

    c = APIClient()
    c.force_authenticate(auditor)

    e = live_election["election"]
    assert c.post(
        f"/api/elections/{e.id}/finalize"
    ).status_code == 403


def test_tampering_holds_the_results(live_election):
    from voting.models import Ballot

    e = live_election["election"]
    session = validate(
        live_election["token"], "V001"
    ).data["vote_session"]

    vote(session, live_election["candidates"][0].id)

    e.status = "closed"
    e.save()

    b = Ballot.objects.first()
    data = bytearray(bytes(b.encrypted_ballot))
    data[0] ^= 1
    b.encrypted_ballot = bytes(data)
    b.save()

    admin = APIClient()
    admin.force_authenticate(live_election["admin"])

    r = admin.post(f"/api/elections/{e.id}/finalize")
    assert r.status_code == 409
    assert r.data["held"] is True
