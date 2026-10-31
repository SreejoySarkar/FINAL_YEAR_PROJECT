from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ElectionEligibleVotersView,
    EligibilityCheckView,
    VoterCSVImportView,
    VoterViewSet,
)

router = DefaultRouter()
router.register("voters", VoterViewSet, basename="voter")

urlpatterns = [
    path("voters/import", VoterCSVImportView.as_view()),
    path(
        "elections/<int:election_id>/eligible-voters",
        ElectionEligibleVotersView.as_view(),
    ),
    path(
        "elections/<int:election_id>/eligibility/check",
        EligibilityCheckView.as_view(),
    ),
    path("", include(router.urls)),
]