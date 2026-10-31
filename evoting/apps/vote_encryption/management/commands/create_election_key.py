from django.core.management.base import BaseCommand

from apps.common.integration import get_election
from apps.vote_encryption.services import create_election_key


class Command(BaseCommand):
    help = "Generate the Paillier key pair for an election (private key encrypted into KEY_STORE_DIR)."

    def add_arguments(self, parser):
        parser.add_argument("election_id")
        parser.add_argument("--bits", type=int, default=None)

    def handle(self, *args, **opts):
        key = create_election_key(get_election(opts["election_id"]), bits=opts["bits"], actor="cli")
        self.stdout.write(self.style.SUCCESS(f"created {key.key_reference} ({key.algorithm})"))
