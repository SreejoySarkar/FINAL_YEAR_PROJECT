from django.urls import path

from . import views

urlpatterns = [
    path("credentials/", views.IssueCredentialView.as_view()),
    path("ring/<str:election_id>/", views.RingView.as_view()),
    path("dev/keypair/", views.DevKeypairView.as_view()),
]
