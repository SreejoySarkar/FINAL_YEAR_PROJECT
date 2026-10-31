"""Creates a complete demo election (stub tables), registers voters, opens voting and writes
pre-built ballots to a JSON file for Postman / Locust.   python manage.py seed_demo --voters 5"""
import json
import random
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.anonymous_authorization.services import get_ring_hex, issue_credential, pop_context
from apps.ballot_management.services import build_ballot_definition
from apps.p1_stub.models import Candidate, Election, Voter
from apps.qr_validation.services import issue_qr_token
from apps.vote_encryption.services import create_election_key, get_active_key
from apps.vote_submission.ballot_builder import build_signed_ballot
from apps.voter_authorization.services import sync_eligibility
from evoting_crypto import lsag


class Command(BaseCommand):
    help = "Seed a demo election with registered voters and pre-built ballots."

    def add_arguments(self, parser):
        parser.add_argument("--voters", type=int, default=5)
        parser.add_argument("--extra", type=int, default=2, help="voters left with an unused QR token")
        parser.add_argument("--out", default="tests/performance/fixtures.json")

    def handle(self, *args, **opts):
        user, _ = get_user_model().objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        user.set_password("admin12345")
        user.save()
        election = Election.objects.create(title="Demo election", status=settings.P1_STATUS_VALUES["registration"])
        candidates = [Candidate.objects.create(election=election, name=n) for n in ("Alice", "Bob", "Carol")]
        total = opts["voters"] + opts["extra"]
        voters = [Voter.objects.create(name=f"Voter {i}", email=f"voter{i}.{election.pk}@example.org") for i in range(total)]
        sync_eligibility(election, actor="cli")
        create_election_key(election, actor="cli")

        keys, spare_tokens = [], []
        for idx, voter in enumerate(voters):
            token, _ = issue_qr_token(voter, election, actor="cli")
            if idx >= opts["voters"]:
                spare_tokens.append(token)
                continue
            x, y = lsag.generate_keypair()
            issue_credential(token=token, public_key_hex=y, possession_proof=lsag.prove_possession(x, pop_context(election.pk)))
            keys.append(x)

        election.status = settings.P1_STATUS_VALUES["voting"]
        election.save()
        definition, ring = build_ballot_definition(election), get_ring_hex(election)
        paillier_public = get_active_key(election).public_key
        entries = []
        for x in keys:
            candidate = random.choice(candidates)
            payload = build_signed_ballot(election_id=election.pk, definition=definition, paillier_public=paillier_public,
                                          ring_hex=ring, private_key=x, candidate_id=str(candidate.pk))
            entries.append({"private_key": format(x, "x"), "candidate_id": str(candidate.pk), "payload": payload})
        out = Path(opts["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"election_id": str(election.pk), "admin": {"username": "admin", "password": "admin12345"},
                                   "voters": entries, "unused_qr_tokens": spare_tokens}, indent=2))
        self.stdout.write(self.style.SUCCESS(f"election {election.pk} ready, fixtures in {out}"))
