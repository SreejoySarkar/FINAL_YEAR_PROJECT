import csv
import io

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from accounts.permissions import roles
from audit.services import log_event
from elections.models import Election
from .models import Eligibility, Voter
from .serializers import (
    AddEligibleSerializer,
    EligibilitySerializer,
    VoterSerializer,
)


class VoterViewSet(viewsets.ModelViewSet):
    queryset = Voter.objects.all().order_by("voter_code")
    serializer_class = VoterSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [roles("org_admin", "election_admin", "auditor")()]
        if self.action == "create":
            return [roles("org_admin", "election_admin")()]
        return [roles("org_admin")()]

    def perform_create(self, serializer):
        v = serializer.save()
        log_event(
            "VOTER_REGISTERED",
            self.request.user,
            {"voter_id": v.id},
            self.request,
        )


class VoterCSVImportView(APIView):
    """POST /api/voters/import"""

    permission_classes = [roles("org_admin")]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=inline_serializer(
            name="VoterCSVImportRequest",
            fields={"file": serializers.FileField()},
        ),
        responses=inline_serializer(
            name="VoterCSVImportResponse",
            fields={
                "created": serializers.IntegerField(),
                "skipped": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            raise ValidationError("Upload a CSV file in the 'file' field.")

        reader = csv.DictReader(
            io.StringIO(f.read().decode("utf-8-sig"))
        )

        created, skipped = 0, 0

        for row in reader:
            _, was_created = Voter.objects.get_or_create(
                voter_code=row["voter_code"].strip(),
                defaults={
                    "full_name": row["full_name"].strip(),
                    "email": row["email"].strip(),
                    "department": row.get("department", "").strip(),
                },
            )

            created += was_created
            skipped += (not was_created)

        log_event(
            "VOTERS_IMPORTED",
            request.user,
            {"created": created, "skipped": skipped},
            request,
        )

        return Response({
            "created": created,
            "skipped": skipped,
        })


class ElectionEligibleVotersView(APIView):
    """GET/POST /api/elections/{id}/eligible-voters"""

    def get_permissions(self):
        if self.request.method == "GET":
            return [roles("election_admin", "org_admin", "auditor")()]
        return [roles("election_admin")()]

    @extend_schema(responses=EligibilitySerializer(many=True))
    def get(self, request, election_id):
        qs = Eligibility.objects.filter(
            election_id=election_id
        ).select_related("voter")

        return Response(
            EligibilitySerializer(qs, many=True).data
        )

    @extend_schema(
        request=AddEligibleSerializer,
        responses=inline_serializer(
            name="EligibleVotersAddedResponse",
            fields={"added": serializers.IntegerField()},
        ),
    )
    def post(self, request, election_id):
        election = get_object_or_404(Election, pk=election_id)

        if election.status != "draft":
            raise ValidationError(
                "Eligible voters can only be changed while the election is in draft."
            )

        s = AddEligibleSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        voters = Voter.objects.filter(
            id__in=s.validated_data["voter_ids"],
            is_active=True,
        )

        Eligibility.objects.bulk_create(
            [
                Eligibility(voter=v, election=election)
                for v in voters
            ],
            ignore_conflicts=True,
        )

        log_event(
            "ELIGIBLE_VOTERS_ADDED",
            request.user,
            {"election_id": election.id, "count": voters.count()},
            request,
        )

        return Response({"added": voters.count()})


class EligibilityCheckView(APIView):
    """
    GET /api/elections/{id}/eligibility/check?voter_code=XYZ

    Used to verify voter ID, membership (is_active)
    and election eligibility.
    """

    permission_classes = [roles("election_admin", "org_admin")]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="voter_code",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
        ],
        responses=inline_serializer(
            name="EligibilityCheckResponse",
            fields={
                "eligible": serializers.BooleanField(),
                "reason": serializers.CharField(allow_null=True),
            },
        ),
    )
    def get(self, request, election_id):
        code = request.query_params.get("voter_code", "")

        voter = Voter.objects.filter(voter_code=code).first()

        if voter is None:
            return Response({
                "eligible": False,
                "reason": "Voter ID not found",
            })

        if not voter.is_active:
            return Response({
                "eligible": False,
                "reason": "Not an active member",
            })

        ok = Eligibility.objects.filter(
            voter=voter,
            election_id=election_id,
            is_eligible=True,
        ).exists()

        return Response({
            "eligible": ok,
            "reason": None if ok else "Not eligible for this election",
        })