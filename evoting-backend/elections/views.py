from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import roles
from audit.services import log_event
from .models import Candidate, Election
from .serializers import CandidateSerializer, ElectionSerializer

READ_ROLES = ("election_admin", "org_admin", "auditor")


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all().order_by("-created_at")
    serializer_class = ElectionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [roles(*READ_ROLES)()]
        return [roles("election_admin")()]

    def perform_create(self, serializer):
        e = serializer.save(created_by=self.request.user)
        log_event(
            "ELECTION_CREATED",
            self.request.user,
            {"election_id": e.id},
            self.request
        )

    def perform_update(self, serializer):
        if serializer.instance.status != "draft":
            raise ValidationError("Only draft elections can be edited.")

        e = serializer.save()
        log_event(
            "ELECTION_UPDATED",
            self.request.user,
            {"election_id": e.id},
            self.request
        )

    def perform_destroy(self, instance):
        if instance.status != "draft":
            raise ValidationError("Only draft elections can be deleted.")

        log_event(
            "ELECTION_DELETED",
            self.request.user,
            {"election_id": instance.id},
            self.request
        )
        instance.delete()

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        with transaction.atomic():
            e = Election.objects.select_for_update().get(pk=pk)

            if e.status != "draft":
                raise ValidationError("Election is not in draft state.")

            if e.candidates.count() < 2:
                raise ValidationError(
                    "Add at least 2 candidates before publishing."
                )

            eligible = e.eligibilities.filter(is_eligible=True).count()

            if eligible == 0:
                raise ValidationError("Add eligible voters before publishing.")

            if e.qr_tokens.count() < eligible:
                raise ValidationError(
                    "Generate QR tokens for all eligible voters before publishing."
                )

            e.status = "published"
            e.save(update_fields=["status"])

        log_event(
            "ELECTION_PUBLISHED",
            request.user,
            {"election_id": e.id},
            request
        )

        return Response(ElectionSerializer(e).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        with transaction.atomic():
            e = Election.objects.select_for_update().get(pk=pk)

            if e.status != "published":
                raise ValidationError(
                    "Only published elections can be closed."
                )

            e.status = "closed"
            e.save(update_fields=["status"])

        log_event(
            "ELECTION_CLOSED",
            request.user,
            {"election_id": e.id},
            request
        )

        return Response(ElectionSerializer(e).data)


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [roles(*READ_ROLES)()]
        return [roles("election_admin")()]

    def _check_draft(self, election):
        if election.status != "draft":
            raise ValidationError(
                "Candidates can only be changed while the election is in draft."
            )

    def perform_create(self, serializer):
        self._check_draft(serializer.validated_data["election"])

        c = serializer.save()

        log_event(
            "CANDIDATE_ADDED",
            self.request.user,
            {"candidate_id": c.id, "election_id": c.election_id},
            self.request
        )

    def perform_update(self, serializer):
        self._check_draft(serializer.instance.election)

        c = serializer.save()

        log_event(
            "CANDIDATE_UPDATED",
            self.request.user,
            {"candidate_id": c.id},
            self.request
        )

    def perform_destroy(self, instance):
        self._check_draft(instance.election)

        log_event(
            "CANDIDATE_DELETED",
            self.request.user,
            {"candidate_id": instance.id},
            self.request
        )

        instance.delete()