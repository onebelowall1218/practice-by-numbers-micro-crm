def test_health_reports_rules_provider_and_demo_clock(client):
    body = client.get("/api/health").json()
    assert body["generation_provider"] == "rules"
    assert body["as_of"] == "2026-09-01"
    assert body["demo_clock"] is True


def test_dashboard_lists_all_twelve_sample_customers_once(client):
    buckets = client.get("/api/dashboard").json()["buckets"]
    names = [c["name"] for bucket in buckets.values() for c in bucket]
    assert len(names) == 12 and len(set(names)) == 12


def test_customer_detail_has_timeline_newest_first_and_clean_notes(client):
    detail = client.get("/api/customers/cust_001").json()
    dates = [i["occurred_at"] for i in detail["interactions"]]
    assert dates == sorted(dates, reverse=True)
    assert "\n" not in detail["interactions"][0]["notes"]
    assert detail["analysis"] is not None


def test_unknown_customer_returns_404(client):
    assert client.get("/api/customers/nope").status_code == 404


def test_adding_an_interaction_stores_raw_notes_and_refreshes_the_analysis(client):
    before = client.get("/api/customers/cust_004").json()["analysis_count"]
    response = client.post(
        "/api/customers/cust_004/interactions",
        json={
            "type": "call",
            "contact_id": "contact_005",
            "notes": "Megan   says the delay\nis back and patients are hanging up again.",
        },
    )
    assert response.status_code == 201
    detail = response.json()
    newest = detail["interactions"][0]
    assert newest["notes"] == "Megan says the delay is back and patients are hanging up again."
    assert newest["ai_summary"]
    assert detail["analysis_count"] == before + 1
    assert detail["analysis"]["trigger"] == "new_interaction"
    assert detail["follow_up"]["source"] == "ai"


def test_contact_from_another_customer_is_rejected(client):
    response = client.post(
        "/api/customers/cust_004/interactions",
        json={"type": "call", "contact_id": "contact_001", "notes": "hello"},
    )
    assert response.status_code == 400


def test_user_can_change_and_complete_the_follow_up(client):
    changed = client.patch(
        "/api/customers/cust_002/follow-up", json={"follow_up_date": "2026-09-20"}
    ).json()
    assert changed["follow_up"] == {"date": "2026-09-20", "source": "user", "completed_at": None}
    done = client.patch("/api/customers/cust_002/follow-up", json={"completed": True}).json()
    assert done["follow_up"]["completed_at"] is not None


def test_draft_message_returns_subject_and_body(client):
    draft = client.post("/api/customers/cust_001/draft-message").json()
    assert draft["subject"] and draft["body"]
