from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.integration import election_phase, get_election, get_voter
from apps.common.utils import client_ip_hash
from apps.common.views import PublicAPIView

from .serializers import GenerateQRSerializer, ValidateQRSerializer
from .services import issue_qr_token, render_qr_png_base64, validate_token


class GenerateQRView(APIView):
    """POST /api/qr/generate/  {"voter_id": 1, "election_id": 1}   (admin)

    Returns the signed token and a PNG QR code (base64). Deliver it ONLY to the voter."""

    def post(self, request):
        data = GenerateQRSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        voter = get_voter(data.validated_data["voter_id"])
        election = get_election(data.validated_data["election_id"])
        token, row = issue_qr_token(voter, election, actor=f"admin:{request.user.pk}")
        return Response({"token": token, "qr_png_base64": render_qr_png_base64(token),
                         "expires_at": row.expires_at}, status=201)


class ValidateQRView(PublicAPIView):
    """POST /api/qr/validate/  {"token": "..."}   (public, does NOT consume the token)"""

    def post(self, request):
        data = ValidateQRSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            row = validate_token(data.validated_data["token"])
        except ApiError as exc:
            log_event("QR_VALIDATION_FAILED", actor="anonymous",
                      details={"reason": exc.code, "client": client_ip_hash(request)})
            raise
        election = get_election(row.election_id)
        return Response({"valid": True, "election_id": str(row.election_id),
                         "phase": election_phase(election), "expires_at": row.expires_at})
