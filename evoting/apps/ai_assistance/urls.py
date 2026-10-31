from django.urls import path

from . import views

urlpatterns = [path("anomalies/<str:election_id>/", views.AnomalyView.as_view())]
