from django.urls import path

from . import views

urlpatterns = [
    path("election-keys/", views.CreateElectionKeyView.as_view()),
    path("election-keys/<str:election_id>/public/", views.PublicKeyView.as_view()),
]
