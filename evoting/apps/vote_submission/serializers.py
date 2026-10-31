from rest_framework import serializers

from evoting_crypto.lsag import MAX_RING


class RingSignatureSerializer(serializers.Serializer):
    key_image = serializers.CharField(max_length=66)
    c0 = serializers.CharField(max_length=80)
    s = serializers.ListField(child=serializers.CharField(max_length=80), min_length=2, max_length=MAX_RING)


class SubmitVoteSerializer(serializers.Serializer):
    election_id = serializers.CharField(max_length=64)
    ciphertexts = serializers.ListField(child=serializers.CharField(max_length=2300), min_length=2, max_length=64)
    proof = serializers.DictField()
    ring_signature = RingSignatureSerializer()


class DemoCastSerializer(serializers.Serializer):
    election_id = serializers.CharField(max_length=64)
    candidate_id = serializers.CharField(max_length=64)
    private_key = serializers.CharField(max_length=64)
