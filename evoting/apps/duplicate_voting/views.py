from rest_framework.response import Response

from apps.anonymous_storage.models import AnonymousBallot
from apps.common.exceptions import ApiError
from apps.common.integration import get_election
from apps.common.views import PublicAPIView
from evoting_crypto import lsag


class KeyImageCheckView(PublicAPIView):
    """GET /api/duplicate/check/?election_id=1&key_image=02...   (public; key images are public data)"""

    def get(self, request):
        election = get_election(request.query_params.get("election_id"))
        try:
            image = lsag.normalize(request.query_params.get("key_image", ""))
        except ValueError:
            raise ApiError("INVALID_KEY_IMAGE", "Key image is malformed.", 400)
        return Response({"used": AnonymousBallot.objects.filter(election=election, key_image=image).exists()})
