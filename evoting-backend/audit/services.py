import hashlib
import json

from django.db import transaction
from django.utils import timezone

from .models import AuditLog


def _client_ip(request):
    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def compute_hash(prev_hash, action, actor_id, details, created_at):
    raw = (
        f"{prev_hash}|{action}|{actor_id}|"
        f"{json.dumps(details, sort_keys=True)}|{created_at.isoformat()}"
    )

    return hashlib.sha256(raw.encode()).hexdigest()


def log_event(action, actor=None, details=None, request=None):
    """
    Call this whenever an important activity happens.
    NEVER store passwords, OTPs, or tokens in audit details.
    """

    details = details or {}

    with transaction.atomic():
        last = (
            AuditLog.objects
            .select_for_update()
            .order_by("-id")
            .first()
        )

        prev_hash = last.event_hash if last else "GENESIS"

        now = timezone.now()
        actor_id = actor.id if actor else None

        return AuditLog.objects.create(
            actor=actor,
            action=action,
            details=details,
            ip_address=_client_ip(request),
            created_at=now,
            prev_hash=prev_hash,
            event_hash=compute_hash(
                prev_hash,
                action,
                actor_id,
                details,
                now
            ),
        )


def verify_chain():
    """
    Returns (True, None) if the chain is valid.
    Otherwise returns (False, ID of the first incorrect record).
    """

    prev = "GENESIS"

    for row in AuditLog.objects.order_by("id"):
        expected = compute_hash(
            prev,
            row.action,
            row.actor_id,
            row.details,
            row.created_at
        )

        if row.prev_hash != prev or row.event_hash != expected:
            return False, row.id

        prev = row.event_hash

    return True, None