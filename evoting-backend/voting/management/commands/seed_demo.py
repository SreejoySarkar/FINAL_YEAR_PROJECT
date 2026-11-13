from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Admin
from elections.models import Candidate, Election
from voters.models import Eligibility, Voter
from voting.helpers import create_token_row


class Command(BaseCommand):
    help = "Create a synthetic LIVE election with fake voters and write tokens.txt"

    def add_arguments(self, parser):
        parser.add_argument("--voters", type=int, default=20)

    def handle(self, *args, **opts):
        admin, created = Admin.objects.get_or_create(
            username="demo_election_admin",
            defaults={"email": "demo_ea@example.com", "role": "election_admin"})
        if created:
            admin.set_password("Pass#12345")
            admin.save()

        now = timezone.now()
        e = Election.objects.create(
            title="Demo election", description="Synthetic data only",
            start_time=now - timedelta(minutes=5), end_time=now + timedelta(days=1),
            status="published", created_by=admin)  # published directly, only for demos

        for name in ("Candidate A", "Candidate B", "Candidate C"):
            Candidate.objects.create(election=e, name=name)

        stamp = now.strftime("%H%M%S")
        lines = []

        for i in range(opts["voters"]):
            v = Voter.objects.create(
                voter_code=f"D{stamp}{i:04d}",
                full_name=f"Demo Voter {i}",
                email=f"demo{stamp}{i}@example.com")

            Eligibility.objects.create(voter=v, election=e)
            _, token = create_token_row(e, v)
            lines.append(f"{token},{v.voter_code}")

        Path("tokens.txt").write_text("\n".join(lines))

        self.stdout.write(self.style.SUCCESS(
            f"Election id {e.id} created. {len(lines)} tokens written to tokens.txt"))