from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from audit.services import log_event
from elections.models import Candidate

from .crypto import receipt_hash
from .models import Ballot
from .serializers import QRValidateSerializer, SubmitVoteSerializer
from .services import (
    SESSION_MAX_AGE,
    VoteError,
    authorize,
    cast_vote,
    check_token,
    make_session,
    read_session,
)


class VoterAPIView(APIView):
    """Base class for voter-facing APIs."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "vote"

    def fail(self, request, error, action="VOTE_REJECTED"):
        if error.code == "already_voted":
            action = "DUPLICATE_VOTE_ATTEMPT"

        log_event(
            action,
            None,
            {
                "reason": error.code,
                "election_id": error.election_id,
                "voter_id": error.voter_id,
            },
            request
        )

        return Response(
            {
                "ok": False,
                "code": error.code,
                "detail": error.message
            },
            status=error.status
        )


class QRValidateView(VoterAPIView):
    """POST /api/qr/validate"""

    @extend_schema(request=QRValidateSerializer)
    def post(self, request):
        s = QRValidateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            row, election, voter = check_token(
                s.validated_data["token"],
                s.validated_data["voter_code"]
            )
        except VoteError as e:
            return self.fail(request, e, "QR_VALIDATION_FAILED")

        log_event(
            "QR_VALIDATED",
            None,
            {
                "election_id": election.id,
                "voter_id": voter.id
            },
            request
        )

        return Response({
            "ok": True,
            "vote_session": make_session(row),
            "expires_in_seconds": SESSION_MAX_AGE,
            "election": {
                "id": election.id,
                "title": election.title
            }
        })


class CheckAuthorizationView(VoterAPIView):
    """POST /api/votes/check-authorization"""

    def post(self, request):
        try:
            _, election, _ = authorize(read_session(request))
        except VoteError as e:
            return self.fail(request, e)

        return Response({
            "ok": True,
            "authorized": True,
            "election": {
                "id": election.id,
                "title": election.title
            }
        })


class BallotView(VoterAPIView):
    """GET /api/elections/{id}/ballot"""

    def get(self, request, election_id):
        try:
            sess = read_session(request)

            if sess["eid"] != election_id:
                raise VoteError(
                    "wrong_election",
                    "This QR code is for another election.",
                    403
                )

            _, election, _ = authorize(sess)

        except VoteError as e:
            return self.fail(request, e)

        candidates = Candidate.objects.filter(
            election=election
        ).order_by("?")

        return Response({
            "election": {
                "id": election.id,
                "title": election.title,
                "description": election.description
            },
            "candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description
                }
                for c in candidates
            ]
        })


class VoteSubmitView(VoterAPIView):
    """POST /api/votes/submit"""

    def post(self, request):
        s = SubmitVoteSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        try:
            sess = read_session(request)
            receipt, election = cast_vote(
                sess, s.validated_data["candidate_id"]
            )
        except VoteError as e:
            return self.fail(request, e)

        log_event(
            "VOTE_CAST",
            None,
            {
                "election_id": election.id,
                "voter_id": sess["vid"]
            },
            request
        )

        return Response({
            "ok": True,
            "receipt": receipt,
            "message": "Your vote was recorded. Keep this receipt."
        }, status=201)


class ConfirmationView(VoterAPIView):
    """GET /api/votes/confirmation?receipt=..."""

    def get(self, request):
        h = receipt_hash(request.query_params.get("receipt", ""))
        ballot = Ballot.objects.filter(
            receipt_hash=h
        ).select_related("election").first()

        if ballot is None:
            return Response({"recorded": False}, status=404)

        return Response({
            "recorded": True,
            "election": ballot.election.title
        })