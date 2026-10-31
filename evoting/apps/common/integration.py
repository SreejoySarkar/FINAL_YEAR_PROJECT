"""The ONLY place that knows about Person 1's tables.

If Person 1's models/columns differ from the defaults, change settings.P1_* (or this file).
No other module imports Person 1's models directly.
"""
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError

from .exceptions import ApiError

REGISTRATION, VOTING, CLOSED, OTHER = "registration", "voting", "closed", "other"


def voter_model():
    return apps.get_model(settings.P1_VOTER_MODEL)


def election_model():
    return apps.get_model(settings.P1_ELECTION_MODEL)


def candidate_model():
    return apps.get_model(settings.P1_CANDIDATE_MODEL)


def _get(model, pk, code, label):
    try:
        return model.objects.get(pk=pk)
    except (model.DoesNotExist, ValueError, TypeError, ValidationError, OverflowError):
        raise ApiError(code, f"{label} not found.", 404)


def get_election(pk):
    return _get(election_model(), pk, "ELECTION_NOT_FOUND", "Election")


def get_voter(pk):
    return _get(voter_model(), pk, "VOTER_NOT_FOUND", "Voter")


def election_phase(election) -> str:
    status = getattr(election, settings.P1_FIELDS["election_status"])
    for phase, value in settings.P1_STATUS_VALUES.items():
        if status == value:
            return phase
    return OTHER


def is_voter_active(voter) -> bool:
    return bool(getattr(voter, settings.P1_FIELDS["voter_active"], True))


def iter_active_voters():
    return voter_model().objects.filter(**{settings.P1_FIELDS["voter_active"]: True}).iterator()


def get_candidates(election) -> list:
    """Candidates in a stable order (primary key) - the index in this list is the ballot option index."""
    filters = {settings.P1_FIELDS["candidate_election"]: election}
    active = settings.P1_FIELDS.get("candidate_active")
    if active:
        filters[active] = True
    return list(candidate_model().objects.filter(**filters).order_by("pk"))


def candidate_label(candidate) -> str:
    return str(getattr(candidate, settings.P1_FIELDS["candidate_label"], candidate))
