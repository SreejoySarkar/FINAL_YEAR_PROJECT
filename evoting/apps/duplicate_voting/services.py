from django.conf import settings

from apps.anonymous_authorization.services import get_ring
from apps.anonymous_storage.models import AnonymousBallot
from apps.common.exceptions import ApiError
from evoting_crypto import lsag


def ensure_key_image_unused(election, key_image: str) -> None:
    if AnonymousBallot.objects.filter(election=election, key_image=key_image).exists():
        raise ApiError("DUPLICATE_VOTE", "A ballot with this key image was already cast.", 409)


def verify_signature_and_check_duplicate(election, message: bytes, signature: dict) -> str:
    """LSAG verification over the frozen ring + election-scoped key-image check.
    Returns the canonical key image. (The DB unique constraint re-checks atomically on insert.)"""
    ring = get_ring(election)
    if len(ring) < settings.MIN_RING_SIZE:
        raise ApiError("RING_TOO_SMALL", "Not enough registered voters to guarantee anonymity.", 409)
    try:
        key_image = lsag.normalize(signature["key_image"])
    except (KeyError, ValueError, TypeError):
        raise ApiError("INVALID_RING_SIGNATURE", "Ring signature is malformed.", 422)
    if not lsag.verify(message, ring, signature, election.pk):
        raise ApiError("INVALID_RING_SIGNATURE", "Ring signature verification failed.", 422)
    ensure_key_image_unused(election, key_image)
    return key_image
