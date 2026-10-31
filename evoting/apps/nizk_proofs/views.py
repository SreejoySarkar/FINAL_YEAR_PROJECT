from rest_framework import serializers
from rest_framework.response import Response

from apps.ballot_management.services import build_ballot_definition
from apps.common.integration import get_election
from apps.common.views import PublicAPIView
from apps.vote_encryption.services import get_active_key
from evoting_crypto import lsag

from .services import verify_ballot_proof


class VerifyProofSerializer(serializers.Serializer):
    election_id = serializers.CharField(max_length=64)
    key_image = serializers.CharField(max_length=66)
    ciphertexts = serializers.ListField(child=serializers.CharField(max_length=2300), min_length=2, max_length=64)
    proof = serializers.DictField()


class VerifyProofView(PublicAPIView):
    """POST /api/nizk/verify/   (public) - lets anyone check a ballot proof without submitting it."""

    def post(self, request):
        data = VerifyProofSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        d = data.validated_data
        election = get_election(d["election_id"])
        pk = get_active_key(election).paillier_public_key()
        try:
            image = lsag.normalize(d["key_image"])
            cts = [int(c, 16) for c in d["ciphertexts"]]
        except ValueError:
            return Response({"valid": False, "reason": "malformed input"})
        ok = verify_ballot_proof(pk, election.pk, build_ballot_definition(election)["hash"], image, cts, d["proof"])
        return Response({"valid": ok})
