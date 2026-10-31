from rest_framework import serializers


class GenerateQRSerializer(serializers.Serializer):
    voter_id = serializers.CharField(max_length=64)
    election_id = serializers.CharField(max_length=64)


class ValidateQRSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=1024)
