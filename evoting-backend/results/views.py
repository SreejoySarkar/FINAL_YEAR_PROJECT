from django.utils import timezone
from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import roles
from audit.models import AuditLog
from audit.services import log_event, verify_chain
from elections.models import Election
from .models import ElectionResult
from .serializers import ResultSerializer
from .services import compute_result, verify_election
from voters.models import Eligibility


ANY_ADMIN = ("election_admin", "org_admin", "auditor")


class TurnoutView(APIView):
    """GET /api/elections/{id}/turnout : numbers for the live dashboard (no candidate counts)"""

    permission_classes = [roles(*ANY_ADMIN)]

    def get(self, request, election_id):
        e = get_object_or_404(Election, pk=election_id)
        eligible = Eligibility.objects.filter(
            election=e,
            is_eligible=True
        )

        total = eligible.count()
        voted = eligible.filter(has_voted=True).count()

        return Response({
            "election": e.title,
            "status": e.status,
            "eligible": total,
            "voted": voted,
            "remaining": total - voted,
            "percent_voted": round(100 * voted / total, 1) if total else 0
        })


class AuditSummaryView(APIView):
    """GET /api/elections/{id}/audit-summary"""

    permission_classes = [roles(*ANY_ADMIN)]

    def get(self, request, election_id):
        e = get_object_or_404(Election, pk=election_id)

        events = AuditLog.objects.filter(
            details__election_id=e.id
        )

        counts = events.values("action").annotate(
            n=Count("id")
        ).order_by("action")

        intact, first_bad = verify_chain()

        return Response({
            "election": e.title,
            "total_events": events.count(),
            "events": {
                c["action"]: c["n"] for c in counts
            },
            "audit_chain_intact": intact,
            "first_bad_record_id": first_bad
        })

class VerifyView(APIView):
    """GET /api/elections/{id}/verify : integrity report"""

    permission_classes = [roles("election_admin", "auditor")]

    def get(self, request, election_id):
        e = get_object_or_404(Election, pk=election_id)
        report = verify_election(e)

        log_event(
            "ELECTION_VERIFIED",
            request.user,
            {"election_id": e.id, "ok": report["ok"]},
            request
        )

        return Response(report)


class FinalizeView(APIView):
    """POST /api/elections/{id}/finalize"""

    permission_classes = [roles("election_admin")]

    def post(self, request, election_id):
        e = get_object_or_404(Election, pk=election_id)

        if e.status != "closed":
            raise ValidationError("Close the election first.")

        existing = ElectionResult.objects.filter(election=e).first()

        if existing and existing.is_published:
            raise ValidationError("Results are already published.")

        outcome = compute_result(e)

        if not outcome["ok"]:
            log_event(
                "RESULTS_HELD",
                request.user,
                {
                    "election_id": e.id,
                    "problems": outcome["report"]["problems"]
                },
                request
            )

            return Response(
                {"held": True, "report": outcome["report"]},
                status=status.HTTP_409_CONFLICT
            )

        result, _ = ElectionResult.objects.update_or_create(
            election=e,
            defaults={
                **outcome["data"],
                "verification": outcome["report"],
                "finalized_by": request.user,
                "finalized_at": timezone.now()
            }
        )

        log_event(
            "RESULTS_FINALIZED",
            request.user,
            {"election_id": e.id, "total_votes": result.total_votes},
            request
        )

        return Response(ResultSerializer(result).data)


class ResultsView(APIView):
    """GET /api/elections/{id}/results : public only AFTER publishing"""

    permission_classes = [AllowAny]

    def get(self, request, election_id):
        result = ElectionResult.objects.filter(
            election_id=election_id
        ).first()

        if result is None:
            return Response({"detail": "No results yet."}, status=404)

        u = request.user
        staff = u.is_authenticated and u.role in ("election_admin", "auditor")

        if not result.is_published and not staff:
            return Response(
                {"detail": "Results are not published yet."},
                status=403
            )

        return Response(ResultSerializer(result).data)


class PublishResultsView(APIView):
    """POST /api/elections/{id}/publish-results"""

    permission_classes = [roles("election_admin")]

    def post(self, request, election_id):
        result = get_object_or_404(
            ElectionResult,
            election_id=election_id
        )

        if result.is_published:
            raise ValidationError("Already published.")

        report = verify_election(result.election)

        if not report["ok"]:
            log_event(
                "RESULTS_HELD",
                request.user,
                {
                    "election_id": election_id,
                    "problems": report["problems"]
                },
                request
            )

            return Response(
                {"held": True, "report": report},
                status=status.HTTP_409_CONFLICT
            )

        result.is_published = True
        result.published_at = timezone.now()
        result.save(update_fields=["is_published", "published_at"])

        log_event(
            "RESULTS_PUBLISHED",
            request.user,
            {"election_id": election_id},
            request
        )

        return Response(ResultSerializer(result).data)   