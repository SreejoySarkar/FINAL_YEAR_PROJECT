import hashlib
import json

from django.db import connection, transaction
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
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(72419301)")

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

def verify_after_checkpoint():
    from .models import AuditRecoveryCheckpoint

    checkpoint = AuditRecoveryCheckpoint.objects.order_by("-id").first()

    if checkpoint is None:
        return False, "No recovery checkpoint exists"

    anchor = AuditLog.objects.filter(
        id=checkpoint.anchor_record_id
    ).first()

    if anchor is None:
        return False, "Checkpoint anchor record does not exist"

    if anchor.event_hash != checkpoint.anchor_event_hash:
        return False, "Checkpoint anchor hash does not match"

    previous_hash = checkpoint.anchor_event_hash

    rows = AuditLog.objects.filter(
        id__gt=checkpoint.anchor_record_id
    ).order_by("id")

    for row in rows:
        expected_hash = compute_hash(
            previous_hash,
            row.action,
            row.actor_id,
            row.details,
            row.created_at
        )

        if row.prev_hash != previous_hash:
            return False, row.id

        if row.event_hash != expected_hash:
            return False, row.id

        previous_hash = row.event_hash

    return True, None
