from rest_framework import serializers

from .models import ElectionResult


class ResultSerializer(serializers.ModelSerializer):
    turnout_percent = serializers.SerializerMethodField()

    class Meta:
        model = ElectionResult
        fields = [
            "election",
            "tally",
            "total_votes",
            "eligible_voters",
            "turnout_percent",
            "winner_ids",
            "verification",
            "is_published",
            "finalized_at",
            "published_at",
        ]

    def get_turnout_percent(self, obj):
        if not obj.eligible_voters:
            return 0

        return round(
            100 * obj.total_votes / obj.eligible_voters,
            1
        )