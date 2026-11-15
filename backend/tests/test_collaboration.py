def test_vote_is_unique_and_can_be_removed(login, customer, make_request):
    item = make_request()
    api = login(customer)
    assert api.post(f"/api/requests/{item.id}/vote/").json() == {"votes": 1, "voted": True}
    assert api.post(f"/api/requests/{item.id}/vote/").json() == {"votes": 1, "voted": True}
    assert api.delete(f"/api/requests/{item.id}/vote/").json() == {"votes": 0, "voted": False}
    assert api.delete(f"/api/requests/{item.id}/vote/").json() == {"votes": 0, "voted": False}


def test_comment_appears_in_detail(login, customer, make_request):
    item = make_request()
    api = login(customer)
    response = api.post(
        f"/api/requests/{item.id}/comments/", {"body": "  Saturday morning.  "}, format="json"
    )
    assert response.status_code == 201
    comments = api.get(f"/api/requests/{item.id}/").json()["comments"]
    assert [
        (c["author_name"], c["author_role"], c["body"], c["is_decision"]) for c in comments
    ] == [("Mariana Costa", "Customer", "Saturday morning.", False)]


def test_empty_comment_is_rejected(login, customer, make_request):
    item = make_request()
    response = login(customer).post(
        f"/api/requests/{item.id}/comments/", {"body": "   "}, format="json"
    )
    assert response.status_code == 400
    assert "body" in response.json()


def test_only_po_marks_decision_and_only_one(login, customer, po, make_request):
    item = make_request()
    api = login(customer)
    first = api.post(f"/api/requests/{item.id}/comments/", {"body": "Card."}, format="json").json()
    second = api.post(f"/api/requests/{item.id}/comments/", {"body": "Cash."}, format="json").json()
    url = f"/api/requests/{item.id}/comments/{first['id']}/decision/"
    assert api.post(url).status_code == 403
    api = login(po)
    assert api.post(url).json()["is_decision"] is True
    again = api.post(f"/api/requests/{item.id}/comments/{second['id']}/decision/")
    assert again.status_code == 409
    detail = api.get(f"/api/requests/{item.id}/").json()
    assert detail["version"] == 2
    assert detail["versions"][0]["summary"] == "Decision recorded"
