from django.conf import settings
from django.db import models


class QRToken(models.Model):
    voter = models.ForeignKey(settings.P1_VOTER_MODEL, on_delete=models.PROTECT, related_name="+")
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    token_hash = models.CharField(max_length=64, unique=True)  # SHA-256 of the signed token; token itself never stored
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "qr_token"
        indexes = [models.Index(fields=["voter", "election"])]
