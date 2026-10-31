from django.conf import settings
from django.http import Http404
from rest_framework.response import Response

from apps.anonymous_authorization.services import get_ring_hex
from apps.ballot_management.services import build_ballot_definition
from apps.common.exceptions import ApiError
from apps.common.integration import get_election
from apps.common.views import PublicSubmitAPIView
from apps.vote_encryption.services import get_active_key

from .ballot_builder import build_signed_ballot
from .serializers import DemoCastSerializer, SubmitVoteSerializer
from .services import submit_vote


class SubmitVoteView(PublicSubmitAPIView):
    """POST /api/votes/submit/   (public, throttled)

    {"election_id": 1, "ciphertexts": ["..", ".."], "proof": {...}, "ring_signature": {"key_image","c0","s":[..]}}
    No login: authorisation is the ring signature. No voter id is accepted or stored."""

    def post(self, request):
        data = SubmitVoteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(submit_vote(**data.validated_data), status=201)


class DemoCastView(PublicSubmitAPIView):
    """POST /api/votes/demo-cast/  {"election_id","candidate_id","private_key"}  - DEMO ONLY.

    Builds + submits a ballot on the server so you can test with Postman without client code.
    The server learns the choice AND the key: never enable ENABLE_DEMO_ENDPOINTS in production."""

    def post(self, request):
        if not settings.ENABLE_DEMO_ENDPOINTS:
            raise Http404
        data = DemoCastSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        election = get_election(data.validated_data["election_id"])
        try:
            private_key = int(data.validated_data["private_key"], 16)
            payload = build_signed_ballot(
                election_id=election.pk, definition=build_ballot_definition(election),
                paillier_public=get_active_key(election).public_key, ring_hex=get_ring_hex(election),
                private_key=private_key, candidate_id=data.validated_data["candidate_id"])
        except ValueError as exc:
            raise ApiError("DEMO_BUILD_FAILED", str(exc), 400)
        return Response(submit_vote(**{k: payload[k] for k in ("election_id", "ciphertexts", "proof", "ring_signature")}), status=201)
