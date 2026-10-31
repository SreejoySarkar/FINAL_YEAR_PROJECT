from django.http import FileResponse
from drf_spectacular.utils import OpenApiTypes, extend_schema, inline_serializer
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from accounts.permissions import roles
from audit.services import log_event
from elections.models import Election
from .models import QRToken
from .services import issue_token


class GenerateQRView(APIView):
    """POST /api/elections/{id}/generate-qr: one token per eligible voter."""

    permission_classes = [roles("election_admin")]

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="GenerateQRResponse",
            fields={
                "created": serializers.IntegerField(),
                "total": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request, election_id):
        election = get_object_or_404(Election, pk=election_id)

        if election.status != "draft":
            raise ValidationError(
                "QR tokens can only be generated before publishing."
            )

        eligible = election.eligibilities.filter(
            is_eligible=True,
            voter__is_active=True,
        ).select_related("voter")

        already = set(
            election.qr_tokens.values_list("voter_id", flat=True)
        )

        created = 0

        for el in eligible:
            if el.voter_id not in already:
                issue_token(election, el.voter)
                created += 1

        log_event(
            "QR_TOKENS_GENERATED",
            request.user,
            {"election_id": election.id, "created": created},
            request,
        )

        return Response({
            "created": created,
            "total": election.qr_tokens.count(),
        })


class DownloadQRView(APIView):
    """GET /api/elections/{id}/voters/{voter_id}/qr"""

    permission_classes = [roles("election_admin", "org_admin")]

    @extend_schema(responses=OpenApiTypes.BINARY)
    def get(self, request, election_id, voter_id):
        tok = get_object_or_404(
            QRToken,
            election_id=election_id,
            voter_id=voter_id,
        )

        log_event(
            "QR_DOWNLOADED",
            request.user,
            {
                "election_id": election_id,
                "voter_id": voter_id,
            },
            request,
        )

        return FileResponse(
            tok.qr_image.open("rb"),
            content_type="image/png",
        )