from django.urls import path

from . import views

urlpatterns = [
    path("submit/", views.SubmitVoteView.as_view()),
    path("demo-cast/", views.DemoCastView.as_view()),
]
