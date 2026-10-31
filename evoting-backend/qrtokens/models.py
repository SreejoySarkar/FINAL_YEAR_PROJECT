import uuid
from django.db import models


class QRToken(models.Model):
    jti = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    election = models.ForeignKey(
        "elections.Election",
        on_delete=models.CASCADE,
        related_name="qr_tokens"
    )

    voter = models.ForeignKey(
        "voters.Voter",
        on_delete=models.CASCADE,
        related_name="qr_tokens"
    )

    token_hash = models.CharField(max_length=64, unique=True)
    qr_image = models.FileField(upload_to="qr/", blank=True)

    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Person 2 will update these fields when a vote is cast
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["election", "voter"],
                name="one_token_per_voter_per_election"
            )
        ]