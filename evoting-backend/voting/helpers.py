from qrtokens.models import QRToken
from qrtokens.services import hash_token, make_signed_token


def create_token_row(election, voter):
    """Demo/test helper: makes a valid QR token without a PNG. Returns (row, token)."""
    row = QRToken(
        election=election,
        voter=voter,
        expires_at=election.end_time
    )

    token = make_signed_token(row.jti, election.id, voter.id)
    row.token_hash = hash_token(token)
    row.save()

    return row, token