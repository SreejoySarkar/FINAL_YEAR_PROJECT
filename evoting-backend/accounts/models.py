from django.contrib.auth.models import AbstractUser
from django.db import models


class Admin(AbstractUser):
    ROLE_CHOICES = [
        ("org_admin", "Org Admin"),
        ("election_admin", "Election Admin"),
        ("auditor", "Auditor"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="election_admin"
    )


class AdminOTP(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)