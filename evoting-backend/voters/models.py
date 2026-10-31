from django.db import models


class Voter(models.Model):
    voter_code = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voter_code} - {self.full_name}"


class Eligibility(models.Model):
    voter = models.ForeignKey(
        Voter,
        on_delete=models.CASCADE,
        related_name="eligibilities"
    )
    election = models.ForeignKey(
        "elections.Election",
        on_delete=models.CASCADE,
        related_name="eligibilities"
    )
    is_eligible = models.BooleanField(default=True)

    # Person 2 will update these fields when a vote is cast
    has_voted = models.BooleanField(default=False)
    voted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["voter", "election"],
                name="unique_voter_election"
            )
        ]