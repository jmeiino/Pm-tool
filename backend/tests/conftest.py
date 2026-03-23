import pytest
from rest_framework.test import APIClient

from tests.factories import ProjectFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def project(user):
    return ProjectFactory(owner=user)
