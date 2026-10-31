from django.urls import path

from . import views

urlpatterns = [path("<str:election_id>/calculate/", views.CalculateResultView.as_view())]
