from django.urls import path

from .views import DownloadQRView, GenerateQRView


urlpatterns = [
    path(
        "elections/<int:election_id>/generate-qr",
        GenerateQRView.as_view(),
    ),
    path(
        "elections/<int:election_id>/voters/<int:voter_id>/qr",
        DownloadQRView.as_view(),
    ),
]