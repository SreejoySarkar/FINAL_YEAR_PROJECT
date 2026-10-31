from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "actor_reference", "election", "action", "details", "previous_hash", "event_hash", "created_at"]
