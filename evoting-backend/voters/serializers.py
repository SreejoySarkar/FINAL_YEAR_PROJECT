from rest_framework import serializers
from .models import Eligibility, Voter


class VoterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = [
            "id",
            "voter_code",
            "full_name",
            "email",
            "department",
            "is_active",
        ]


class EligibilitySerializer(serializers.ModelSerializer):
    voter = VoterSerializer(read_only=True)

    class Meta:
        model = Eligibility
        fields = ["id", "voter", "is_eligible", "has_voted"]


class AddEligibleSerializer(serializers.Serializer):
    voter_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )