from django.urls import path

from . import views

urlpatterns = [
    path("<str:election_id>/", views.PublicResultView.as_view()),
    path("<str:election_id>/publish/", views.PublishResultView.as_view()),
]
