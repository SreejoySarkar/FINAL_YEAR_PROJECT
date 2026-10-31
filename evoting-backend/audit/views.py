from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, serializers

from accounts.permissions import roles
from .models import AuditLog
from .services import verify_chain


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

    def get(self, request):
        ok, bad_id = verify_chain()

        return Response({
            "intact": ok,
            "first_bad_record_id": bad_id,
        })