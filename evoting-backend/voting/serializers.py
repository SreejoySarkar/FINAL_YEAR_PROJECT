from rest_framework import serializers


class QRValidateSerializer(serializers.Serializer):
    token = serializers.CharField()
    voter_code = serializers.CharField()


class SubmitVoteSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField()