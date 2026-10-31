from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Append-only, hash-chained security log: event_hash = SHA256(previous_hash, event)."""

    actor_reference = models.CharField(max_length=128)
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=64, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    previous_hash = models.CharField(max_length=64)
    event_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "audit_log"
        ordering = ["id"]
        indexes = [models.Index(fields=["election", "action"])]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionError("audit log entries are immutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("audit log entries cannot be deleted")
