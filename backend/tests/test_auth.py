import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from apps.collaboration.models import Membership, Role, Workspace


def test_me_requires_session(api, db):
    assert api.get("/api/auth/me/").status_code == 403


def test_login_returns_profile(api, customer):
    response = api.post(
        "/api/auth/login/", {"username": "mariana", "password": "pw-12345"}, format="json"
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": customer.id,
        "username": "mariana",
        "name": "Mariana Costa",
        "role": "customer",
        "role_label": "Customer",
        "workspace": {"id": customer.membership.workspace_id, "name": "Acme"},
    }
    assert api.get("/api/auth/me/").json()["username"] == "mariana"


def test_login_wrong_password(api, customer):
    response = api.post(
        "/api/auth/login/", {"username": "mariana", "password": "nope"}, format="json"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid username or password."}
    assert api.get("/api/auth/me/").status_code == 403


def test_login_without_membership_is_refused(api, db):
    User.objects.create_user(username="ghost", password="pw-12345")
    response = api.post(
        "/api/auth/login/", {"username": "ghost", "password": "pw-12345"}, format="json"
    )
    assert response.status_code == 403
    assert api.get("/api/auth/me/").status_code == 403


def test_logout_ends_session(login, customer):
    api = login(customer)
    assert api.post("/api/auth/logout/").status_code == 204
    assert api.get("/api/auth/me/").status_code == 403


def test_csrf_endpoint_sets_cookie(api, db):
    response = api.get("/api/auth/csrf/")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies


def test_login_enforces_csrf(db, customer):
    from rest_framework.test import APIClient

    strict = APIClient(enforce_csrf_checks=True)
    response = strict.post(
        "/api/auth/login/", {"username": "mariana", "password": "pw-12345"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_seed_demo_creates_personas_and_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")
    assert Workspace.objects.count() == 1
    roles = dict(Membership.objects.values_list("user__username", "role"))
    assert roles == {
        "mariana": Role.CUSTOMER,
        "pedro": Role.CUSTOMER,
        "rui": Role.PRODUCT_OWNER,
        "catarina": Role.DEVELOPER,
        "duarte": Role.PROJECT_MANAGER,
    }
    assert User.objects.get(username="rui").check_password("featurehub")
    assert User.objects.get(username="rui").get_full_name() == "Rui Almeida"
