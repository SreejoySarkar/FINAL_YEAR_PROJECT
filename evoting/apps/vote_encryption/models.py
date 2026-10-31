from django.conf import settings
from django.db import models
from django.db.models import Q

from evoting_crypto.paillier import PaillierPublicKey


class ElectionKey(models.Model):
    """PUBLIC Paillier key only. The private key lives encrypted on disk (evoting_crypto.key_management)."""

    ACTIVE, RETIRED = "ACTIVE", "RETIRED"
    election = models.ForeignKey(settings.P1_ELECTION_MODEL, on_delete=models.PROTECT, related_name="+")
    algorithm = models.CharField(max_length=32)
    public_key = models.JSONField()
    key_reference = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=10, choices=[(ACTIVE, ACTIVE), (RETIRED, RETIRED)], default=ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "election_key"
        constraints = [models.UniqueConstraint(fields=["election"], condition=Q(status="ACTIVE"), name="uq_one_active_key_per_election")]

    def paillier_public_key(self) -> PaillierPublicKey:
        return PaillierPublicKey.from_dict(self.public_key)
