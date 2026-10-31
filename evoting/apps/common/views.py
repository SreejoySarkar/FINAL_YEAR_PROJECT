from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .throttles import PublicThrottle, SubmitThrottle


class PublicAPIView(APIView):
    """No login, no CSRF/session handling, IP-based throttling. Anything here is world-reachable."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PublicThrottle]


class PublicSubmitAPIView(PublicAPIView):
    throttle_classes = [SubmitThrottle]
