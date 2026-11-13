from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer

from accounts.permissions import roles
from .models import AuditLog
from .services import verify_chain, verify_after_checkpoint


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_username",
            "action",
            "details",
            "ip_address",
            "created_at",
            "prev_hash",
            "event_hash",
        ]


class AuditLogListView(generics.ListAPIView):
    permission_classes = [roles("auditor", "org_admin")]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all().order_by("-id")


class AuditVerifyView(APIView):
    permission_classes = [roles("auditor", "org_admin")]

    @extend_schema(
        responses=inline_serializer(
            name="AuditVerifyResponse",
            fields={
                "intact": serializers.BooleanField(),
                "first_bad_record_id": serializers.IntegerField(
                    allow_null=True,
                ),
            },
        ),
    )
    def get(self, request):
        ok, bad_id = verify_chain()

        return Response({
            "intact": ok,
            "first_bad_record_id": bad_id,
        })


class AuditRecoveryVerifyView(APIView):
    permission_classes = [roles("auditor", "org_admin")]

    def get(self, request):
        from .models import AuditRecoveryCheckpoint

        checkpoint = AuditRecoveryCheckpoint.objects.order_by("-id").first()

        if checkpoint is None:
            return Response(
                {"error": "No recovery checkpoint exists"},
                status=404
            )

        result, issue = verify_after_checkpoint()

        return Response({
            "post_checkpoint_intact": result,
            "first_bad_record_id": issue if isinstance(issue, int) else None,
            "verification_error": issue if isinstance(issue, str) else None,
            "checkpoint_record_id": checkpoint.anchor_record_id,
            "historical_broken_links": checkpoint.historical_broken_links
        })