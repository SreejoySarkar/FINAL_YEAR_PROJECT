from django.conf import settings
from django.db import models


class AuthorizationCredential(models.Model):
    """One anonymous voting public key per registered voter.

    DELIBERATELY has no voter column: nothing here links a key to a person.
    The ring for an election is the set of ACTIVE public keys."""

    ACTIVE, REVOKED = "ACTIVE", "REVOKED"
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    credential_reference = models.CharField(max_length=64, unique=True)
    public_key = models.CharField(max_length=66)
    status = models.CharField(max_length=10, choices=[(ACTIVE, ACTIVE), (REVOKED, REVOKED)], default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "authorization_credential"
        constraints = [models.UniqueConstraint(fields=["election", "public_key"], name="uq_credential_election_key")]
