import uuid

from django.conf import settings
from django.db import models


class AnonymousBallot(models.Model):
    """NO voter column - by design. Random UUID keys and minute-resolution timestamps
    avoid leaking submission order/time."""

    PENDING, VERIFIED, REJECTED = "PENDING", "VERIFIED", "REJECTED"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    election_key = models.ForeignKey("vote_encryption.ElectionKey", on_delete=models.PROTECT, related_name="+")
    key_image = models.CharField(max_length=66)
    ring_signature = models.JSONField()
    proof_data = models.JSONField()   # {"definition_hash", "ring_hash", "proof": {...}}
    verification_status = models.CharField(max_length=10, default=VERIFIED,
                                           choices=[(s, s) for s in (PENDING, VERIFIED, REJECTED)])
    submitted_at = models.DateTimeField()

    class Meta:
        db_table = "anonymous_ballot"
        constraints = [models.UniqueConstraint(fields=["election", "key_image"], name="uq_ballot_election_key_image")]


class EncryptedVoteComponent(models.Model):
    ballot = models.ForeignKey(AnonymousBallot, on_delete=models.CASCADE, related_name="components")
    option_index = models.PositiveSmallIntegerField()
    ciphertext = models.TextField()   # hex
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "encrypted_vote_component"
        constraints = [models.UniqueConstraint(fields=["ballot", "option_index"], name="uq_component_ballot_option")]
