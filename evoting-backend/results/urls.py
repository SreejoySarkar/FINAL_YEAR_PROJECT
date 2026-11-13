from django.urls import path

from .views import (
    AuditSummaryView,
    FinalizeView,
    PublishResultsView,
    ResultsView,
    TurnoutView,
    VerifyView,
)

urlpatterns = [
    path("elections/<int:election_id>/turnout", TurnoutView.as_view()),
    path("elections/<int:election_id>/audit-summary", AuditSummaryView.as_view()),
    path("elections/<int:election_id>/verify", VerifyView.as_view()),
    path("elections/<int:election_id>/finalize", FinalizeView.as_view()),
    path("elections/<int:election_id>/results", ResultsView.as_view()),
    path("elections/<int:election_id>/publish-results", PublishResultsView.as_view()),
]