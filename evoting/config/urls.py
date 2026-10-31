from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/qr/", include("apps.qr_validation.urls")),
    path("api/voter-authorization/", include("apps.voter_authorization.urls")),
    path("api/anonymous-auth/", include("apps.anonymous_authorization.urls")),
    path("api/duplicate/", include("apps.duplicate_voting.urls")),
    path("api/ballots/", include("apps.ballot_management.urls")),
    path("api/votes/", include("apps.vote_submission.urls")),
    path("api/encryption/", include("apps.vote_encryption.urls")),
    path("api/nizk/", include("apps.nizk_proofs.urls")),
    path("api/authorization/", include("apps.authorization_management.urls")),
    path("api/audit/", include("apps.audit_management.urls")),
    path("api/verification/", include("apps.election_verification.urls")),
    path("api/result-calculation/", include("apps.result_calculation.urls")),
    path("api/results/", include("apps.result_publication.urls")),
    path("api/ai/", include("apps.ai_assistance.urls")),
]
