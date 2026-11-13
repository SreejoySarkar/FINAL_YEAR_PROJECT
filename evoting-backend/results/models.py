from django.conf import settings
from django.db import models
from django.utils import timezone


class ElectionResult(models.Model):
    election = models.OneToOneField(
        "elections.Election",
        on_delete=models.CASCADE,
        related_name="result"
    )

    tally = models.JSONField()
    total_votes = models.PositiveIntegerField()
    eligible_voters = models.PositiveIntegerField()
    winner_ids = models.JSONField(default=list)
    verification = models.JSONField()

    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL
    )

    finalized_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)