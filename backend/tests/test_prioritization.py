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


def test_stale_version_wins_over_other_errors(login, po, make_request):
    item = make_request()
    api = login(po)
    assess(api, item, version=1, status="under_review")
    # Quem vê uma versão antiga recebe 412, e não um erro calculado sobre dados que não viu.
    assert assess(api, item, version=1, status="under_review").status_code == 412
    assert assess(api, item, version=1, impact=9).status_code == 412


def test_customer_history_hides_internal_assessment(login, customer, po, make_request):
    item = make_request()
    api = login(po)
    assess(api, item, version=1, impact=5, effort=8, status="under_review")
    assess(api, item, version=2, impact=4)
    api.post(
        "/api/prioritization/reorder/",
        {"request": item.id, "before": None, "reason": "contract with Acme Lda"},
        format="json",
    )
    raw = login(customer).get(f"/api/requests/{item.id}/")
    for secret in ("impact", "effort", "Priority moved", "Acme Lda"):
        assert secret not in raw.content.decode()
    assert [v["summary"] for v in raw.json()["versions"]] == [
        "Status → Under review",
        "Request created",
    ]
    team = login(po).get(f"/api/requests/{item.id}/").json()["versions"]
    assert team[0]["summary"] == "Priority moved manually: contract with Acme Lda"
    assert len(team) == 4


def test_malformed_input_is_a_400_not_a_crash(login, po, customer, category, make_request):
    item = make_request()
    api = login(po)
    assert api.patch(f"/api/requests/{item.id}/assessment/", [1], format="json").status_code == 400
    assert api.post("/api/requests/", [1], format="json").status_code == 400
    assert api.post(f"/api/requests/{item.id}/comments/", [1], format="json").status_code == 400
    assert api.post("/api/auth/login/", [1], format="json").status_code == 400
    nul = api.post(f"/api/requests/{item.id}/comments/", {"body": "a\u0000b"}, format="json")
    assert nul.status_code == 201 and nul.json()["body"] == "ab"
    created = api.post(
        "/api/requests/",
        {"title": "T\u0000itle", "description": "d", "category": category.id, "tags": []},
        format="json",
    )
    assert created.status_code == 201 and created.json()["title"] == "Title"
    assert api.get("/api/requests/?search=%23").json()["count"] == 0


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


def move(api, item, before, reason="contract commitment"):
    return api.post(
        "/api/prioritization/reorder/",
        {"request": item.id, "before": before.id if before else None, "reason": reason},
        format="json",
    )


def test_manual_reorder_needs_reason_and_is_recorded(ranked):
    api, a, b, c = ranked
    no_reason = move(api, b, a, reason=" ")
    assert no_reason.status_code == 400 and "reason" in no_reason.json()
    assert move(api, b, a).status_code == 200
    table = rows(api)
    assert [r["title"] for r in table] == ["B", "A", "C"]
    assert (table[0]["manual"], table[0]["override_reason"]) == (True, "contract commitment")
    history = api.get(f"/api/requests/{b.id}/").json()["versions"][0]["summary"]
    assert history == "Priority moved manually: contract commitment"


def test_every_move_takes_effect_even_over_another_manual_row(ranked):
    api, a, b, c = ranked
    move(api, b, a)  # B, A, C
    assert move(api, a, b).status_code == 200  # A volta ao topo, por cima de B (manual)
    assert [r["title"] for r in rows(api)] == ["A", "B", "C"]
    move(api, c, a)
    assert [r["title"] for r in rows(api)] == ["C", "A", "B"]
    move(api, c, None)  # para o fim
    assert [r["title"] for r in rows(api)] == ["A", "B", "C"]


def test_move_inside_a_category_keeps_the_global_order_sane(ranked, workspace, make_request):
    from apps.requests.models import Category

    api, a, b, c = ranked
    other = Category.objects.create(workspace=workspace, name="Interface")
    d = make_request(title="D", category=other)
    e = make_request(title="E", category=other)
    # Na vista filtrada (D, E), o PO põe E antes de D: não pode saltar para o topo global.
    assert move(api, e, d).status_code == 200
    assert [r["title"] for r in rows(api, f"?category={other.id}")] == ["E", "D"]
    assert [r["title"] for r in rows(api)] == ["A", "B", "C", "E", "D"]


def test_reorder_rejects_bad_targets(ranked, login, po):
    from apps.requests.models import FeatureRequest, Status

    api, a, b, c = ranked
    assert move(api, a, a).status_code == 400
    FeatureRequest.objects.filter(pk=c.pk).update(status=Status.RELEASED)
    assert move(api, c, a).status_code == 400
    assert move(api, a, c).status_code == 400
    assert api.post("/api/prioritization/reorder/", [1], format="json").status_code == 400


def test_suggestion_explains_and_accept_clears_overrides(ranked):
    api, a, b, c = ranked
    move(api, c, a, reason="CEO asked")
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
        {"request": item.id, "before": None, "reason": "x"},
        format="json",
    )
    assert response.status_code == 404
