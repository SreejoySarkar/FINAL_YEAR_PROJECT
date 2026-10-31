from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.integration import get_election

from .services import calculate_result


class CalculateSerializer(serializers.Serializer):
    passphrase = serializers.CharField(required=False, allow_blank=True, write_only=True)


class CalculateResultView(APIView):
    """POST /api/result-calculation/<election_id>/calculate/   (admin; election must be closed)"""

    def post(self, request, election_id):
        data = CalculateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        result = calculate_result(get_election(election_id), actor=f"admin:{request.user.pk}",
                                  passphrase=data.validated_data.get("passphrase"))
        return Response({"election_id": str(result.election_id), "verification_status": result.verification_status,
                         "valid_ballots": result.valid_ballots, "rejected_ballots": result.rejected_ballots,
                         "result_data": result.result_data, "published": False})
