from django.urls import path

from .views import AuditLogListView, AuditVerifyView, AuditRecoveryVerifyView


urlpatterns = [
    path("audit-logs", AuditLogListView.as_view()),
    path("audit-logs/verify", AuditVerifyView.as_view()),
    path("audit-logs/verify-recovery", AuditRecoveryVerifyView.as_view()),
]