import pytest

from apps.prioritization.models import Vote
from apps.prioritization.services import score


def assess(api, item, **data):
    return api.patch(f"/api/requests/{item.id}/assessment/", data, format="json")


@pytest.mark.parametrize(
    ("votes", "impact", "effort", "expected"),
    [(13, 5, 8, 8.1), (4, 2, 3, 2.7), (9, 3, 5, 5.4), (7, None, None, None), (3, 2, 0, None)],
)
def test_score(votes, impact, effort, expected):
    assert score(votes, impact, effort) == expected


def test_only_po_can_assess(login, customer, developer, pm, make_request):
    item = make_request()
    for user in (customer, developer, pm):
        assert assess(login(user), item, version=1, impact=3).status_code == 403


def test_assessment_updates_and_records_version(login, po, make_request):
    item = make_request()
    api = login(po)
    response = assess(api, item, version=1, impact=5, effort=8, status="under_review")
    assert response.status_code == 200
    data = response.json()
    assert (data["status"], data["version"]) == ("under_review", 2)
    assert data["assessment"] == {"impact": 5, "effort": 8}
    assert data["versions"][0]["summary"] == "Status → Under review; impact 5, effort 8 pts"
    assert data["versions"][0]["actor_name"] == "Rui Almeida"


def test_stale_version_is_refused_with_412(login, po, make_request):
    item = make_request()
    api = login(po)
    assert assess(api, item, version=1, impact=4).status_code == 200
    stale = assess(api, item, version=1, impact=2)
    assert stale.status_code == 412
    assert stale.json()["version"] == 2
    assert api.get(f"/api/requests/{item.id}/").json()["assessment"]["impact"] == 4


def test_missing_version_and_bad_values(login, po, make_request):
    item = make_request()
    api = login(po)
    assert "version" in assess(api, item, impact=3).json()
    assert assess(api, item, version=1, impact=6).status_code == 400
    assert assess(api, item, version=1, effort=0).status_code == 400
    assert assess(api, item, version=1, impact="x").status_code == 400


def test_status_must_follow_allowed_transitions(login, po, make_request):
    item = make_request()
    api = login(po)
    skipped = assess(api, item, version=1, status="released")
    assert skipped.status_code == 400
    assert "status" in skipped.json()
    assert assess(api, item, version=1, status="under_review").status_code == 200
    assert assess(api, item, version=2, status="rejected").status_code == 200
    assert assess(api, item, version=3, status="planned").status_code == 400


def test_detail_hides_assessment_from_customers(login, customer, developer, po, make_request):
    item = make_request()
    assess(login(po), item, version=1, impact=5, effort=8)
    as_customer = login(customer).get(f"/api/requests/{item.id}/").json()
    assert as_customer["assessment"] is None and as_customer["can_assess"] is False
    as_dev = login(developer).get(f"/api/requests/{item.id}/").json()
    assert as_dev["assessment"] == {"impact": 5, "effort": 8} and as_dev["can_assess"] is False
    as_po = login(po).get(f"/api/requests/{item.id}/").json()
    assert as_po["can_assess"] is True
    assert [s["value"] for s in as_po["next_statuses"]] == ["under_review"]


def test_prioritization_is_po_only(login, customer, developer, pm):
    for user in (customer, developer, pm):
        api = login(user)
        assert api.get("/api/prioritization/").status_code == 403
        assert api.get("/api/prioritization/suggestion/").status_code == 403
        assert api.post("/api/prioritization/reorder/", {}, format="json").status_code == 403


@pytest.fixture
def ranked(login, po, customer, customer2, developer, make_request):
    """Três pedidos: A score 3.0, B score 1.0, C sem estimativa (2 votos)."""
    a = make_request(title="A")
    b = make_request(title="B")
    c = make_request(title="C")
    for user in (customer, customer2, developer):
        Vote.objects.create(request=a, user=user)
    Vote.objects.create(request=b, user=customer)
    Vote.objects.create(request=c, user=customer)
    Vote.objects.create(request=c, user=customer2)
    api = login(po)
    assess(api, a, version=1, impact=2, effort=2)
    assess(api, b, version=1, impact=3, effort=3)
    return api, a, b, c


def rows(api, query=""):
    return api.get(f"/api/prioritization/{query}").json()


def test_table_orders_by_score_with_missing_estimates_last(ranked):
    api, a, b, c = ranked
    assert [(r["title"], r["votes"], r["score"], r["manual"]) for r in rows(api)] == [
        ("A", 3, 3.0, False),
        ("B", 1, 1.0, False),
        ("C", 2, None, False),
    ]


def test_manual_reorder_needs_reason_and_is_recorded(ranked):
    api, a, b, c = ranked
    no_reason = api.post(
        "/api/prioritization/reorder/", {"request": b.id, "position": 0}, format="json"
    )
    assert no_reason.status_code == 400 and "reason" in no_reason.json()
    done = api.post(
        "/api/prioritization/reorder/",
        {"request": b.id, "position": 0, "reason": "contract commitment"},
        format="json",
    )
    assert done.status_code == 200
    table = rows(api)
    assert [r["title"] for r in table] == ["B", "A", "C"]
    assert (table[0]["manual"], table[0]["override_reason"]) == (True, "contract commitment")
    history = api.get(f"/api/requests/{b.id}/").json()["versions"][0]["summary"]
    assert history == "Priority moved manually: contract commitment"


def test_suggestion_explains_and_accept_clears_overrides(ranked):
    api, a, b, c = ranked
    api.post(
        "/api/prioritization/reorder/",
        {"request": c.id, "position": 0, "reason": "CEO asked"},
        format="json",
    )
    suggestion = api.get("/api/prioritization/suggestion/").json()
    assert "No external AI service" in suggestion["basis"]
    assert [(i["title"], i["reason"]) for i in suggestion["items"]] == [
        ("A", "Score 3.0: 3 votes × impact 2 ÷ effort 2 pts."),
        ("B", "Score 1.0: 1 vote × impact 3 ÷ effort 3 pts."),
        ("C", "Needs an impact and effort estimate first."),
    ]
    assert [r["title"] for r in rows(api)] == ["C", "A", "B"]
    assert api.post("/api/prioritization/suggestion/accept/").status_code == 204
    assert [(r["title"], r["manual"]) for r in rows(api)] == [
        ("A", False),
        ("B", False),
        ("C", False),
    ]


def test_table_filters_by_category_and_skips_closed(ranked, workspace, make_request):
    from apps.requests.models import Category, FeatureRequest, Status

    api, a, b, c = ranked
    other = Category.objects.create(workspace=workspace, name="Interface")
    make_request(title="D", category=other)
    FeatureRequest.objects.filter(pk=b.pk).update(status=Status.REJECTED)
    FeatureRequest.objects.filter(pk=c.pk).update(status=Status.RELEASED)
    assert [r["title"] for r in rows(api)] == ["A", "D"]
    assert [r["title"] for r in rows(api, f"?category={other.id}")] == ["D"]


def test_reorder_rejects_request_from_other_workspace(login, outsider, make_request):
    item = make_request()
    response = login(outsider).post(
        "/api/prioritization/reorder/",
        {"request": item.id, "position": 0, "reason": "x"},
        format="json",
    )
    assert response.status_code == 404
