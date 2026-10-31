"""LOCAL DEVELOPMENT STAND-IN for Person 1's tables. Not part of the deliverable.
Disable with USE_P1_STUB=False and point P1_*_MODEL at Person 1's real models."""
from django.db import models


class Voter(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Election(models.Model):
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default="upcoming")  # upcoming | ongoing | closed

    def __str__(self):
        return self.title


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
