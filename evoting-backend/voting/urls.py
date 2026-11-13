from django.urls import path

from .views import (
    BallotView,
    CheckAuthorizationView,
    ConfirmationView,
    QRValidateView,
    VoteSubmitView,
)

urlpatterns = [
    path("qr/validate", QRValidateView.as_view()),
    path("votes/check-authorization", CheckAuthorizationView.as_view()),
    path("elections/<int:election_id>/ballot", BallotView.as_view()),
    path("votes/submit", VoteSubmitView.as_view()),
    path("votes/confirmation", ConfirmationView.as_view()),
]