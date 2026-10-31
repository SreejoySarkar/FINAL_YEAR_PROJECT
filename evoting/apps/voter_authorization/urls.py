from django.urls import path

from . import views

urlpatterns = [
    path("sync/", views.SyncEligibilityView.as_view()),
    path("eligibility/", views.EligibilityListView.as_view()),
    path("eligibility/<int:pk>/", views.EligibilityUpdateView.as_view()),
]
