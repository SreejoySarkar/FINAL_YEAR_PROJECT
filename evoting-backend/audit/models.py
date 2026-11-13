from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    action = models.CharField(max_length=60)

    details = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField()

    prev_hash = models.CharField(max_length=64)

    event_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ["id"]
class AuditRecoveryCheckpoint(models.Model):
    anchor_record_id = models.PositiveBigIntegerField(unique=True)
    anchor_event_hash = models.CharField(max_length=64)
    historical_broken_links = models.PositiveIntegerField()
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]