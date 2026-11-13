
import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone
import threading
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from audit.models import AuditLog, AuditRecoveryCheckpoint
from audit.services import log_event
from elections.models import Candidate, Election
from results.services import verify_election
from testkit import session_for, validate, vote
from voters.models import Eligibility
from voting.models import Ballot

from elections.models import Candidate, Election
from results.services import verify_election
from testkit import session_for, validate, vote
from voters.models import Eligibility
from voting.models import Ballot


def test_valid_qr_gives_session(live_election):
    r = validate(live_election["token"], "V001")
    assert r.status_code == 200 and r.data["ok"] is True


def test_tampered_token_rejected(live_election):
    t = live_election["token"]
    bad = t[:-2] + ("AA" if not t.endswith("AA") else "BB")
    r = validate(bad, "V001")
    assert r.status_code == 400 and r.data["code"] == "invalid"


def test_wrong_voter_code_rejected(live_election):
    r = validate(live_election["token"], "SOMEONE-ELSE")
    assert r.status_code == 403 and r.data["code"] == "identity_mismatch"


def test_expired_qr_rejected(live_election):
    row = live_election["row"]
    row.expires_at = timezone.now() - timedelta(minutes=1)
    row.save()
    assert validate(live_election["token"], "V001").data["code"] == "expired"


def test_closed_election_rejected(live_election):
    e = live_election["election"]
    e.status = "closed"
    e.save()
    assert validate(live_election["token"], "V001").data["code"] == "election_not_open"


def test_inactive_voter_rejected(live_election):
    v = live_election["voter"]
    v.is_active = False
    v.save()
    assert validate(live_election["token"], "V001").data["code"] == "not_eligible"


def test_vote_once_then_reuse_rejected(live_election):
    session = session_for(live_election)
    cid = live_election["candidates"][0].id
    assert vote(session, cid).status_code == 201
    assert vote(session, cid).status_code == 409
    assert validate(live_election["token"], "V001").status_code == 409
    assert Ballot.objects.count() == 1
    live_election["row"].refresh_from_db()
    assert live_election["row"].is_used is True
    assert Eligibility.objects.get(voter=live_election["voter"]).has_voted is True


def test_submit_without_session_rejected(live_election):
    r = vote("", live_election["candidates"][0].id)
    assert r.status_code == 401 and r.data["code"] == "no_session"


def test_candidate_from_other_election_rejected(live_election):
    other = Election.objects.create(
        title="Other",
        start_time=timezone.now(),
        end_time=timezone.now() + timedelta(days=1),
        created_by=live_election["admin"]
    )
    foreign = Candidate.objects.create(election=other, name="Foreign")
    r = vote(session_for(live_election), foreign.id)
    assert r.status_code == 400 and r.data["code"] == "bad_candidate"
    assert Ballot.objects.count() == 0
    assert Eligibility.objects.get(voter=live_election["voter"]).has_voted is False


def test_ballot_table_has_no_voter_columns():
    names = {f.name for f in Ballot._meta.get_fields()}
    assert not any("voter" in n or "user" in n or "created" in n for n in names)


def test_ciphertext_does_not_contain_plaintext(live_election):
    vote(session_for(live_election), live_election["candidates"][0].id)
    assert b"candidate_id" not in bytes(Ballot.objects.first().encrypted_ballot)


def test_tampered_ballot_is_detected(live_election):
    # Create a valid audit event to use as the checkpoint anchor.
    log_event("TEST_CHECKPOINT_ANCHOR")

    anchor = AuditLog.objects.order_by("-id").first()

    AuditRecoveryCheckpoint.objects.create(
        anchor_record_id=anchor.id,
        anchor_event_hash=anchor.event_hash,
        historical_broken_links=0,
        reason="Test database recovery checkpoint",
    )

    # Submit a valid vote.
    vote(session_for(live_election), live_election["candidates"][0].id)

    # Verification should pass before tampering.
    assert verify_election(live_election["election"])["ok"] is True

    # Tamper with the encrypted ballot.
    b = Ballot.objects.first()
    data = bytearray(bytes(b.encrypted_ballot))
    data[-1] ^= 1
    b.encrypted_ballot = bytes(data)
    b.save()

    # Verification should detect the tampering.
    assert verify_election(live_election["election"])["ok"] is False


@pytest.mark.django_db(transaction=True)
def test_concurrent_double_submit_creates_one_ballot(live_election):
    session = session_for(live_election)
    cid = live_election["candidates"][0].id
    codes = []

    def attempt():
        try:
            codes.append(vote(session, cid).status_code)
        finally:
            connection.close()

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert codes.count(201) == 1
    assert Ballot.objects.filter(election=live_election["election"]).count() == 1
