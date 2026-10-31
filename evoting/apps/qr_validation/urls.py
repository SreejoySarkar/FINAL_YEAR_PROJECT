from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.GenerateQRView.as_view()),
    path("validate/", views.ValidateQRView.as_view()),
]
