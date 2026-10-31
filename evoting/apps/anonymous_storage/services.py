from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.exceptions import ApiError

from .models import AnonymousBallot, EncryptedVoteComponent


def store_ballot(*, election, election_key, key_image, ring_signature, proof_data, ciphertext_hex) -> AnonymousBallot:
    """Atomic insert. The UNIQUE(election, key_image) constraint is the final, race-proof
    guard against double voting (two simultaneous requests: exactly one wins)."""
    try:
        with transaction.atomic():
            ballot = AnonymousBallot.objects.create(
                election=election, election_key=election_key, key_image=key_image,
                ring_signature=ring_signature, proof_data=proof_data,
                submitted_at=timezone.now().replace(second=0, microsecond=0),
            )
            EncryptedVoteComponent.objects.bulk_create([
                EncryptedVoteComponent(ballot=ballot, option_index=i, ciphertext=c) for i, c in enumerate(ciphertext_hex)])
    except IntegrityError:
        raise ApiError("DUPLICATE_VOTE", "A ballot with this key image was already cast.", 409)
    return ballot
