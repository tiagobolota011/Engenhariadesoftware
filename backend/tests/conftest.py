import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.collaboration.models import Membership, Role, Workspace


@pytest.fixture
def workspace(db):
    return Workspace.objects.create(name="Acme")


@pytest.fixture
def other_workspace(db):
    return Workspace.objects.create(name="Other")


@pytest.fixture
def make_user(db, workspace):
    def _make(username, role=Role.CUSTOMER, ws=None, name=None):
        first, _, last = (name or username.title()).partition(" ")
        user = User.objects.create_user(
            username=username, password="pw-12345", first_name=first, last_name=last
        )
        Membership.objects.create(user=user, workspace=ws or workspace, role=role)
        return user

    return _make


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def login(api):
    def _login(user):
        api.force_login(user)
        return api

    return _login


@pytest.fixture
def customer(make_user):
    return make_user("mariana", Role.CUSTOMER, name="Mariana Costa")


@pytest.fixture
def customer2(make_user):
    return make_user("pedro", Role.CUSTOMER, name="Pedro Nunes")


@pytest.fixture
def po(make_user):
    return make_user("rui", Role.PRODUCT_OWNER, name="Rui Almeida")


@pytest.fixture
def developer(make_user):
    return make_user("catarina", Role.DEVELOPER, name="Catarina Reis")


@pytest.fixture
def pm(make_user):
    return make_user("duarte", Role.PROJECT_MANAGER, name="Duarte Fernandes")


@pytest.fixture
def outsider(make_user, other_workspace):
    return make_user("eve", Role.PRODUCT_OWNER, ws=other_workspace, name="Eve Outside")
