import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.p1_stub.models import Candidate, Election, Voter


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="admin", password="pw", is_staff=True)
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def election(db):
    e = Election.objects.create(title="Test election", status="upcoming")
    for name in ("Alice", "Bob", "Carol"):
        Candidate.objects.create(election=e, name=name)
    return e


@pytest.fixture
def voters(db):
    return [Voter.objects.create(name=f"v{i}", email=f"v{i}@example.org") for i in range(4)]
