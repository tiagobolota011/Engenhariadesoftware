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


def test_only_po_marks_decision_and_can_move_or_remove_it(login, customer, po, make_request):
    item = make_request()
    api = login(customer)
    first = api.post(f"/api/requests/{item.id}/comments/", {"body": "Card."}, format="json").json()
    second = api.post(f"/api/requests/{item.id}/comments/", {"body": "Cash."}, format="json").json()
    url = f"/api/requests/{item.id}/comments/{first['id']}/decision/"
    assert api.post(url).status_code == 403
    assert api.delete(url).status_code == 403
    api = login(po)
    assert api.post(url).json()["is_decision"] is True

    def decisions():
        detail = api.get(f"/api/requests/{item.id}/").json()
        return [c["body"] for c in detail["comments"] if c["is_decision"]], detail

    # Enganou-se no comentário: marcar outro move a decisão (continua a haver só uma).
    assert api.post(f"/api/requests/{item.id}/comments/{second['id']}/decision/").status_code == 200
    marked, detail = decisions()
    assert marked == ["Cash."]
    assert detail["versions"][0]["summary"] == "Decision changed"
    assert (
        api.delete(f"/api/requests/{item.id}/comments/{second['id']}/decision/").status_code == 200
    )
    marked, detail = decisions()
    assert marked == []
    assert detail["versions"][0]["summary"] == "Decision removed"
    assert detail["version"] == 4


def test_comment_by_former_member_does_not_break_detail(login, customer, customer2, make_request):
    item = make_request()
    login(customer2).post(f"/api/requests/{item.id}/comments/", {"body": "Bye."}, format="json")
    customer2.membership.delete()
    comments = login(customer).get(f"/api/requests/{item.id}/").json()["comments"]
    assert [(c["body"], c["author_role"]) for c in comments] == [("Bye.", "Former member")]
