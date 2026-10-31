from django.urls import path

from .views import AuditLogListView, AuditVerifyView


urlpatterns = [
    path("audit-logs", AuditLogListView.as_view()),
    path("audit-logs/verify", AuditVerifyView.as_view()),
]