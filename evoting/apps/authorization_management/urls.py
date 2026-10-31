from django.urls import path

from . import views

urlpatterns = [
    path("<str:election_id>/summary/", views.AuthorizationSummaryView.as_view()),
    path("<str:election_id>/credentials/", views.CredentialListView.as_view()),
    path("credentials/<str:credential_reference>/revoke/", views.RevokeCredentialView.as_view()),
]
