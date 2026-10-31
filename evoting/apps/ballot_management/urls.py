from django.urls import path

from . import views

urlpatterns = [path("<str:election_id>/", views.BallotView.as_view())]
