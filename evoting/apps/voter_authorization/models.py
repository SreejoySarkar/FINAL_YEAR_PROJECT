from django.conf import settings
from django.db import models


class VoterEligibility(models.Model):
    voter = models.ForeignKey(settings.P1_VOTER_MODEL, on_delete=models.PROTECT, related_name="+")
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    is_eligible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "voter_eligibility"
        constraints = [models.UniqueConstraint(fields=["voter", "election"], name="uq_eligibility_voter_election")]
