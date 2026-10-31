from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response

from .models import Candidate
from .serializers import CandidateSerializer
from .views import CandidateViewSet, ElectionViewSet


router = DefaultRouter()

router.register("elections", ElectionViewSet, basename="election")
router.register("candidates", CandidateViewSet, basename="candidate")


@api_view(["GET"])
def election_candidates(request, election_id):
    """
    GET /api/elections/{id}/candidates
    Also used by Person 2 for the ballot.
    """
    data = CandidateSerializer(
        Candidate.objects.filter(election_id=election_id),
        many=True
    ).data

    return Response(data)


urlpatterns = [
    path(
        "elections/<int:election_id>/candidates",
        election_candidates
    ),
    path("", include(router.urls)),
]