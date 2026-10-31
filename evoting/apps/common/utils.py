from django.conf import settings

from evoting_crypto import hashing


def pseudonym(voter_pk) -> str:
    """Stable, non-reversible reference for a voter, used only in registration audit events."""
    return hashing.hmac_hex(settings.PSEUDONYM_SECRET, f"voter:{voter_pk}")[:24]


def client_ip_hash(request) -> str:
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return hashing.hmac_hex(settings.PSEUDONYM_SECRET, f"ip:{ip}")[:16]


def parse_hex_list(values) -> list[int]:
    return [int(v, 16) for v in values]
