from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.integration import get_election
from apps.common.views import PublicAPIView

from .services import create_election_key, get_active_key


class CreateKeySerializer(serializers.Serializer):
    election_id = serializers.CharField(max_length=64)
    bits = serializers.IntegerField(required=False, min_value=512, max_value=4096)
    passphrase = serializers.CharField(required=False, write_only=True)


class CreateElectionKeyView(APIView):
    """POST /api/encryption/election-keys/  {"election_id": 1}   (admin; 2048-bit keygen takes a few seconds)"""

    def post(self, request):
        data = CreateKeySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        election = get_election(data.validated_data["election_id"])
        key = create_election_key(election, bits=data.validated_data.get("bits"),
                                  passphrase=data.validated_data.get("passphrase"), actor=f"admin:{request.user.pk}")
        return Response({"key_reference": key.key_reference, "algorithm": key.algorithm, "public_key": key.public_key}, status=201)


class PublicKeyView(PublicAPIView):
    """GET /api/encryption/election-keys/<election_id>/public/"""

    def get(self, request, election_id):
        key = get_active_key(get_election(election_id))
        return Response({"election_id": str(key.election_id), "algorithm": key.algorithm,
                         "key_reference": key.key_reference, "public_key": key.public_key})
