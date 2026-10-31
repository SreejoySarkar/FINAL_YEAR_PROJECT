from rest_framework import serializers
from .models import Candidate, Election


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ["id", "election", "name", "description"]


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = [
            "id",
            "title",
            "description",
            "eligibility_criteria",
            "start_time",
            "end_time",
            "status",
            "created_at",
            "candidates",
        ]
        read_only_fields = ["status", "created_at"]

    def validate(self, data):
        start = data.get(
            "start_time",
            getattr(self.instance, "start_time", None)
        )

        end = data.get(
            "end_time",
            getattr(self.instance, "end_time", None)
        )

        if start and end and end <= start:
            raise serializers.ValidationError(
                "end_time must be after start_time."
            )

        return data