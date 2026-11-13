from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path(
        "",
        RedirectView.as_view(url=reverse_lazy("swagger-ui"), permanent=False),
        name="home",
    ),
    path("django-admin/", admin.site.urls),

    path("api/", include("accounts.urls")),
    path("api/", include("elections.urls")),
    path("api/", include("voters.urls")),
    path("api/", include("qrtokens.urls")),
    path("api/", include("audit.urls")),
    path("api/", include("voting.urls")),
    path("api/", include("results.urls")),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )