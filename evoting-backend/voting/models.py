import uuid

from django.db import models


class Ballot(models.Model):
    """
    One encrypted vote.
    Deliberately has NO voter field and NO timestamp.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    election = models.ForeignKey(
        "elections.Election",
        on_delete=models.PROTECT,
        related_name="ballots"
    )

    nonce = models.BinaryField()
    encrypted_ballot = models.BinaryField()
    integrity_hash = models.CharField(max_length=64)
    receipt_hash = models.CharField(max_length=64, unique=True)