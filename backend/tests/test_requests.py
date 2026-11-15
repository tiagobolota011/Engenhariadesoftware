from apps.requests.models import FeatureRequest, Status


def body(category, **over):
    data = {
        "title": "Schedule my order for later",
        "description": "I'd like to choose a delivery date and time.",
        "category": category.id,
        "tags": ["Scheduling", "#mobile", "scheduling"],
        "importance": "Weekly groceries.",
    }
    data.update(over)
    return data


def test_list_requires_session(api, db):
    assert api.get("/api/requests/").status_code == 403


def test_create_request(login, customer, category):
    response = login(customer).post("/api/requests/", body(category), format="json")
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "REQ-001"
    assert data["status"] == "submitted"
    assert data["status_label"] == "Submitted"
    assert data["tags"] == ["mobile", "scheduling"]
    assert data["author_name"] == "Mariana Costa"
    assert data["version"] == 1
    assert [(v["number"], v["summary"]) for v in data["versions"]] == [(1, "Request created")]
    assert data["votes"] == 0 and data["voted"] is False


def test_create_numbers_are_sequential_per_workspace(login, customer, category, make_request):
    make_request()
    response = login(customer).post("/api/requests/", body(category), format="json")
    assert response.json()["key"] == "REQ-002"


def test_create_reports_each_missing_field(login, customer, category):
    response = login(customer).post("/api/requests/", {"title": " ", "tags": []}, format="json")
    assert response.status_code == 400
    assert set(response.json()) == {"title", "description", "category"}
    assert FeatureRequest.objects.count() == 0


def test_create_rejects_category_from_other_workspace(login, customer, other_workspace):
    from apps.requests.models import Category

    foreign = Category.objects.create(workspace=other_workspace, name="Secret")
    response = login(customer).post("/api/requests/", body(foreign), format="json")
    assert response.status_code == 400
    assert "category" in response.json()


def test_list_is_empty_page_when_nothing_exists(login, customer):
    data = login(customer).get("/api/requests/").json()
    assert data["count"] == 0 and data["results"] == []


def test_list_sorted_by_votes_and_marks_my_vote(login, customer, customer2, make_request):
    from apps.prioritization.models import Vote

    first = make_request(title="Dark mode")
    second = make_request(title="Export order history to PDF")
    Vote.objects.create(request=second, user=customer)
    Vote.objects.create(request=second, user=customer2)
    Vote.objects.create(request=first, user=customer2)
    results = login(customer).get("/api/requests/").json()["results"]
    assert [(r["title"], r["votes"], r["voted"]) for r in results] == [
        ("Export order history to PDF", 2, True),
        ("Dark mode", 1, False),
    ]


def test_list_filters(login, customer, customer2, workspace, make_request):
    from apps.requests.models import Category

    interface = Category.objects.create(workspace=workspace, name="Interface")
    make_request(title="Dark mode", category=interface, tags=("theme",))
    mine = make_request(title="Schedule an order in advance")
    other = make_request(title="Guest checkout", author=customer2, tags=("checkout",))
    FeatureRequest.objects.filter(pk=other.pk).update(status=Status.PLANNED)
    api = login(customer)

    def titles(query):
        return {r["title"] for r in api.get(f"/api/requests/?{query}").json()["results"]}

    assert titles("search=schedule") == {"Schedule an order in advance"}
    assert titles("search=theme") == {"Dark mode"}
    assert titles(f"category={interface.id}") == {"Dark mode"}
    assert titles("status=planned") == {"Guest checkout"}
    assert titles("mine=1") == {"Dark mode", "Schedule an order in advance"}
    assert titles("date=7d") == {"Dark mode", "Schedule an order in advance", "Guest checkout"}
    assert mine.key == "REQ-002"


def test_mine_includes_requests_i_voted_with_role(login, customer, customer2, make_request):
    from apps.prioritization.models import Vote

    theirs = make_request(title="Guest checkout", author=customer2)
    make_request(title="Dark mode")
    Vote.objects.create(request=theirs, user=customer)
    results = login(customer).get("/api/requests/?mine=1").json()["results"]
    assert {(r["title"], r["my_role"]) for r in results} == {
        ("Guest checkout", "voted"),
        ("Dark mode", "created"),
    }


def test_similar_requests(login, customer, make_request):
    make_request(title="Schedule an order in advance", tags=("scheduling",))
    make_request(title="Recurring weekly orders", tags=("scheduling",))
    make_request(title="Dark mode", tags=("theme",))
    api = login(customer)
    found = api.get("/api/requests/similar/?q=Schedule my order&tags=scheduling").json()
    assert [r["title"] for r in found] == [
        "Schedule an order in advance",
        "Recurring weekly orders",
    ]
    assert api.get("/api/requests/similar/?q=ab").json() == []


def test_detail_and_workspace_isolation(login, customer, outsider, make_request):
    item = make_request()
    assert login(customer).get(f"/api/requests/{item.id}/").json()["key"] == "REQ-001"
    api = login(outsider)
    assert api.get(f"/api/requests/{item.id}/").status_code == 404
    assert api.get("/api/requests/").json()["count"] == 0
    assert api.post(f"/api/requests/{item.id}/vote/").status_code == 404
    assert (
        api.post(f"/api/requests/{item.id}/comments/", {"body": "hi"}, format="json").status_code
        == 404
    )
    assert (
        api.patch(
            f"/api/requests/{item.id}/assessment/", {"version": 1, "impact": 3}, format="json"
        ).status_code
        == 404
    )


def test_categories_are_scoped(login, customer, category, other_workspace):
    from apps.requests.models import Category

    Category.objects.create(workspace=other_workspace, name="Secret")
    assert login(customer).get("/api/categories/").json() == [
        {"id": category.id, "name": "Ordering"}
    ]


def test_public_roadmap_exposes_only_title_and_category(login, customer, make_request):
    planned = make_request(title="Export order history to PDF")
    make_request(title="Still submitted")
    FeatureRequest.objects.filter(pk=planned.pk).update(status=Status.PLANNED)
    data = login(customer).get("/api/roadmap/public/").json()
    assert data == {
        "planned": [
            {"id": planned.id, "title": "Export order history to PDF", "category": "Ordering"}
        ],
        "in_progress": [],
        "released": [],
    }
