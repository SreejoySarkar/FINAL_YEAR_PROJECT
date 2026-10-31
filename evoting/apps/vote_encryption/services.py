from django.conf import settings

from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.integration import REGISTRATION, election_phase
from evoting_crypto import key_management, paillier

from .models import ElectionKey


def create_election_key(election, *, bits=None, passphrase=None, actor="system") -> ElectionKey:
    bits = bits or settings.PAILLIER_KEY_BITS
    passphrase = passphrase or settings.ELECTION_KEY_PASSPHRASE
    if not passphrase:
        raise ApiError("PASSPHRASE_REQUIRED", "A key passphrase must be provided.", 400)
    if election_phase(election) != REGISTRATION:
        raise ApiError("ELECTION_PHASE_INVALID", "Keys can only be created before voting starts.", 409)
    if ElectionKey.objects.filter(election=election, status=ElectionKey.ACTIVE).exists():
        raise ApiError("KEY_EXISTS", "This election already has an active key.", 409)
    private = paillier.generate_keypair(bits)
    reference = key_management.new_key_reference()
    key_management.store_private_key(private, reference, passphrase, settings.KEY_STORE_DIR)
    row = ElectionKey.objects.create(election=election, algorithm=f"paillier-{bits}",
                                     public_key=private.public.to_dict(), key_reference=reference)
    log_event("ELECTION_KEY_CREATED", election=election, actor=actor,
              details={"key_reference": reference, "algorithm": row.algorithm})
    return row


def get_active_key(election) -> ElectionKey:
    key = ElectionKey.objects.filter(election=election, status=ElectionKey.ACTIVE).first()
    if key is None:
        raise ApiError("NO_ELECTION_KEY", "This election has no encryption key yet.", 409)
    return key


def encrypt_one_hot(pk, option_index: int, option_count: int):
    """Returns (ciphertexts, plaintexts, randomness) for a one-hot vector."""
    if not 0 <= option_index < option_count:
        raise ApiError("INVALID_OPTION", "Selected option does not exist.", 400)
    plaintexts = [1 if i == option_index else 0 for i in range(option_count)]
    encrypted = [pk.encrypt(m) for m in plaintexts]
    return [c for c, _ in encrypted], plaintexts, [r for _, r in encrypted]
