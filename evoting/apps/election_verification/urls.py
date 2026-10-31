from django.urls import path

from . import views

urlpatterns = [
    path("<str:election_id>/run/", views.RunVerificationView.as_view()),
    path("<str:election_id>/public-data/", views.PublicBallotListView.as_view()),
]
