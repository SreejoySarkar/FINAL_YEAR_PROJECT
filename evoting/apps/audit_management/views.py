from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import verify_chain


class AuditLogListView(ListAPIView):
    """GET /api/audit/logs/?election_id=&action=   (admin)"""

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.all().order_by("-id")
        if self.request.query_params.get("election_id"):
            qs = qs.filter(election_id=self.request.query_params["election_id"])
        if self.request.query_params.get("action"):
            qs = qs.filter(action=self.request.query_params["action"])
        return qs


class VerifyChainView(APIView):
    """GET /api/audit/verify-chain/   (admin)"""

    def get(self, request):
        return Response(verify_chain())
