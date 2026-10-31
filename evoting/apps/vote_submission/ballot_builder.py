"""Client-side ballot construction. Used by tools/voter_client.py, the demo endpoint and tests.
In production this logic runs in the voter's browser/app - the server must never see the choice."""
from apps.ballot_management.services import proof_context, signature_message
from apps.nizk_proofs.services import generate_ballot_proof
from evoting_crypto import lsag
from evoting_crypto.paillier import PaillierPublicKey


def build_signed_ballot(*, election_id, definition: dict, paillier_public: dict, ring_hex: list[str],
                        private_key: int, candidate_id: str) -> dict:
    pk = PaillierPublicKey.from_dict(paillier_public)
    options = definition["options"]
    option_index = next((o["option_index"] for o in options if o["candidate_id"] == str(candidate_id)), None)
    if option_index is None:
        raise ValueError("candidate is not on the ballot")
    my_key = lsag.public_key_of(private_key)
    if my_key not in ring_hex:
        raise ValueError("your public key is not in the ring")
    plaintexts = [1 if o["option_index"] == option_index else 0 for o in options]
    encrypted = [pk.encrypt(m) for m in plaintexts]
    ciphertexts = [c for c, _ in encrypted]
    randomness = [r for _, r in encrypted]
    image = lsag.key_image(private_key, election_id)
    proof = generate_ballot_proof(pk, election_id, definition["hash"], image, ciphertexts, plaintexts, randomness)
    ct_hex = [format(c, "x") for c in ciphertexts]
    ring = [lsag.decompress(h) for h in ring_hex]
    signature = lsag.sign(signature_message(election_id, definition["hash"], ct_hex), ring, ring_hex.index(my_key),
                          private_key, election_id)
    return {"election_id": str(election_id), "ciphertexts": ct_hex, "proof": proof, "ring_signature": signature}
