from rest_framework import serializers


class IssueCredentialSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=1024)
    public_key = serializers.CharField(min_length=66, max_length=66)
    possession_proof = serializers.DictField(child=serializers.CharField(max_length=80))
