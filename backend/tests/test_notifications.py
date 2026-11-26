"""Menções e notificações (SCRUM-87 · UC-08, UC-09)."""

import pytest

from apps.collaboration.models import Mention, Notification
from apps.collaboration.notifications import mentioned_usernames


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("@rui can you look?", ["rui"]),
        ("Thanks @Rui, and @catarina.", ["rui", "catarina"]),
        ("@rui @RUI @rui!", ["rui"]),
        ("@ana.silva please", ["ana.silva"]),
        ("mail me at mariana@example.com", []),
        ("no mentions here", []),
        ("just an @ sign", []),
    ],
)
def test_mentioned_usernames(body, expected):
    assert mentioned_usernames(body) == expected


def comment(api, item, body):
    response = api.post(f"/api/requests/{item.id}/comments/", {"body": body}, format="json")
    assert response.status_code == 201
    return response.json()


def test_mention_notifies_member_with_link_to_request(login, customer, po, make_request):
    item = make_request()
    comment(login(customer), item, "@rui can we have this by Friday?")
    assert Mention.objects.filter(user=po).count() == 1

    data = login(po).get("/api/notifications/").json()
    assert data["unread"] == 1
    [n] = data["results"]
    assert n["kind"] == "mention"
    assert n["request_id"] == item.id
    assert n["actor_name"] == "Mariana Costa"
    assert n["message"] == f"Mariana Costa mentioned you on {item.key} {item.title}"
    assert n["read"] is False


def test_mentions_ignore_self_unknown_and_other_workspaces(login, customer, outsider, make_request):
    item = make_request()
    comment(login(customer), item, "@mariana @nobody @eve hello")
    assert Mention.objects.count() == 0
    assert Notification.objects.count() == 0
    assert login(outsider).get("/api/notifications/unread/").json() == {"unread": 0}


def test_repeated_mention_in_one_comment_notifies_once(login, customer, po, make_request):
    item = make_request()
    comment(login(customer), item, "@rui @RUI @rui")
    assert Notification.objects.filter(recipient=po).count() == 1


def test_status_change_notifies_author_but_not_the_po(login, customer, po, make_request):
    item = make_request()
    api = login(po)
    response = api.patch(
        f"/api/requests/{item.id}/assessment/",
        {"version": 1, "status": "under_review"},
        format="json",
    )
    assert response.status_code == 200
    [n] = Notification.objects.all()
    assert n.recipient == customer
    assert n.kind == "status"
    assert n.message == f"{item.key} {item.title} is now Under review"


def test_estimate_only_change_does_not_notify(login, po, make_request):
    item = make_request()
    login(po).patch(
        f"/api/requests/{item.id}/assessment/", {"version": 1, "impact": 3}, format="json"
    )
    assert Notification.objects.count() == 0


def test_po_own_request_status_change_does_not_notify_po(login, po, make_request):
    item = make_request(author=po)
    login(po).patch(
        f"/api/requests/{item.id}/assessment/",
        {"version": 1, "status": "under_review"},
        format="json",
    )
    assert Notification.objects.count() == 0


def test_decision_notifies_author_once(login, customer, po, make_request):
    item = make_request()
    first = comment(login(customer), item, "Card.")
    api = login(po)
    url = f"/api/requests/{item.id}/comments/{first['id']}/decision/"
    api.post(url)
    api.post(url)  # já é a decisão: nada muda, nada é notificado
    [n] = Notification.objects.all()
    assert (n.recipient, n.kind) == (customer, "decision")


def test_mark_one_and_all_as_read(login, customer, po, make_request):
    item = make_request()
    api = login(customer)
    comment(api, item, "@rui first")
    comment(api, item, "@rui second")
    api = login(po)
    newest, oldest = api.get("/api/notifications/").json()["results"]
    read = api.post(f"/api/notifications/{oldest['id']}/read/").json()
    assert read["read"] is True
    assert api.get("/api/notifications/unread/").json() == {"unread": 1}
    unread_only = api.get("/api/notifications/?unread=1").json()["results"]
    assert [n["id"] for n in unread_only] == [newest["id"]]
    assert api.post("/api/notifications/read-all/").json() == {"unread": 0}
    assert api.get("/api/notifications/").json()["unread"] == 0


def test_cannot_read_someone_elses_notification(login, customer, po, developer, make_request):
    item = make_request()
    comment(login(customer), item, "@rui look")
    n = Notification.objects.get()
    assert login(developer).post(f"/api/notifications/{n.id}/read/").status_code == 404
    n.refresh_from_db()
    assert n.read_at is None


def test_notifications_require_a_session(api):
    assert api.get("/api/notifications/").status_code == 403


def test_members_lists_only_own_workspace(login, customer, po, outsider):
    members = login(customer).get("/api/members/").json()
    assert [(m["username"], m["name"], m["role_label"]) for m in members] == [
        ("mariana", "Mariana Costa", "Customer"),
        ("rui", "Rui Almeida", "Product Owner"),
    ]
