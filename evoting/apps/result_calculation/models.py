from django.conf import settings
from django.db import models


class ElectionResult(models.Model):
    PENDING, VERIFIED, FAILED = "PENDING", "VERIFIED", "FAILED"
    election = models.OneToOneField(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    result_data = models.JSONField()
    valid_ballots = models.PositiveIntegerField()
    rejected_ballots = models.PositiveIntegerField()
    verification_status = models.CharField(max_length=10, default=PENDING,
                                           choices=[(s, s) for s in (PENDING, VERIFIED, FAILED)])
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "election_result"
