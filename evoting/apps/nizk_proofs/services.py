from apps.ballot_management.services import proof_context
from evoting_crypto import nizk


def generate_ballot_proof(pk, election_id, definition_hash, key_image, ciphertexts, plaintexts, randomness) -> dict:
    return nizk.prove_one_hot(pk, proof_context(election_id, definition_hash, key_image), ciphertexts, plaintexts, randomness)


def verify_ballot_proof(pk, election_id, definition_hash, key_image, ciphertexts, proof) -> bool:
    return nizk.verify_one_hot(pk, proof_context(election_id, definition_hash, key_image), ciphertexts, proof)
