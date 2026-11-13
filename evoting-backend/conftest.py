from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from audit.models import AuditLog, AuditRecoveryCheckpoint
from audit.services import log_event

from accounts.models import Admin
from elections.models import Candidate, Election
from voters.models import Eligibility, Voter
from voting.helpers import create_token_row


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


@pytest.fixture
def live_election(db):
    admin = Admin.objects.create_user(
        username="ea",
        email="ea@x.com",
        password="Pass#12345",
        role="election_admin"
    )

    now = timezone.now()
    e = Election.objects.create(
        title="Test",
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        status="published",
        created_by=admin
    )

    candidates = [
        Candidate.objects.create(election=e, name=n)
        for n in ("A", "B")
    ]

    voter = Voter.objects.create(
        voter_code="V001",
        full_name="Test Voter",
        email="v1@x.com"
    )

    Eligibility.objects.create(voter=voter, election=e)
    row, token = create_token_row(e, voter)

    # Establish a trusted baseline for the test audit chain.
    log_event("TEST_RECOVERY_CHECKPOINT_ANCHOR")

    anchor = AuditLog.objects.order_by("-id").first()

    AuditRecoveryCheckpoint.objects.create(
        anchor_record_id=anchor.id,
        anchor_event_hash=anchor.event_hash,
        historical_broken_links=0,
        reason="Initial trusted checkpoint for test database",
    )

    return {
        "admin": admin,
        "election": e,
        "candidates": candidates,
        "voter": voter,
        "row": row,
        "token": token
    }