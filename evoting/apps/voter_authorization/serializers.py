from rest_framework import serializers

from .models import VoterEligibility


class EligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VoterEligibility
        fields = ["id", "voter", "election", "is_eligible", "created_at"]
        read_only_fields = ["id", "voter", "election", "created_at"]


class SyncSerializer(serializers.Serializer):
    election_id = serializers.CharField(max_length=64)
