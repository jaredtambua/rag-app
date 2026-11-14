"""Part 2.3: question limits and rate limiting."""

import pytest

from conftest import headers, make_pdf, new_visitor, upload

BUSY = "The demo is very busy. Please try again later."


def ask(client, visitor, question="what is this?", extra=None):
    hdrs = headers(visitor)
    hdrs.update(extra or {})
    return client.post("/ask", json={"question": question}, headers=hdrs)


def test_twentieth_question_ok_twenty_first_refused(client):
    v = new_visitor()
    for _ in range(20):
        assert ask(client, v).status_code == 200
    response = ask(client, v)
    assert response.status_code == 429
    assert response.json()["detail"] == (
        "You have reached the limit of 20 questions per hour. "
        "Please try again in 60 minutes."
    )
    assert response.headers["Retry-After"] == "3600"


def test_asking_works_again_when_the_window_moves(client, clock):
    v = new_visitor()
    for _ in range(20):
        ask(client, v)
        clock.advance(10)  # first question at t0, last at t0+190
    assert ask(client, v).status_code == 429
    clock.advance(3600 - 200 - 1)  # t0 + 3599: first still inside the hour
    assert ask(client, v).status_code == 429
    clock.advance(2)  # t0 + 3601: first has left the window, only it
    assert ask(client, v).status_code == 200
    assert ask(client, v).status_code == 429


def test_retry_after_counts_down(client, clock):
    v = new_visitor()
    for _ in range(20):
        ask(client, v)
    clock.advance(1000)
    response = ask(client, v)
    assert response.headers["Retry-After"] == "2600"
    assert "44 minutes" in response.json()["detail"]


def test_over_long_question_is_400_and_costs_nothing(client):
    v = new_visitor()
    assert ask(client, v, "x" * 500).status_code == 200
    for _ in range(25):
        response = ask(client, v, "x" * 501)
        assert response.status_code == 400
        assert response.json()["detail"] == "Questions can be up to 500 characters."
    # None of the refused questions used up quota: 19 more still fit.
    for _ in range(19):
        assert ask(client, v).status_code == 200
    assert ask(client, v).status_code == 429


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_empty_question_is_400_and_costs_nothing(client, question):
    v = new_visitor()
    for _ in range(25):
        response = ask(client, v, question)
        assert response.status_code == 400
        assert response.json()["detail"] == "Please enter a question."
    for _ in range(20):
        assert ask(client, v).status_code == 200


def test_missing_visitor_id_costs_nothing_and_is_400(client):
    for _ in range(3):
        assert client.post("/ask", json={"question": "hi"}).status_code == 400


def test_per_network_address_limit_uses_last_forwarded_entry(client):
    # Three visitors of 20 fill the 60 per hour allowed for one address.
    # The first entry of X-Forwarded-For is client-made, so it is ignored.
    for i in range(3):
        v = new_visitor()
        for _ in range(20):
            xff = {"X-Forwarded-For": f"10.0.0.{i}, 203.0.113.7"}
            assert ask(client, v, extra=xff).status_code == 200

    fourth = ask(client, new_visitor(), extra={"X-Forwarded-For": "1.1.1.1, 203.0.113.7"})
    assert fourth.status_code == 429
    assert fourth.json()["detail"] == BUSY
    assert "Retry-After" in fourth.headers

    other_address = ask(
        client, new_visitor(), extra={"X-Forwarded-For": "1.1.1.1, 198.51.100.9"}
    )
    assert other_address.status_code == 200


def test_total_ask_ceiling_across_everyone(client, monkeypatch):
    import config

    monkeypatch.setattr(config, "ASK_LIMIT_TOTAL", 5)
    for i in range(5):
        xff = {"X-Forwarded-For": f"192.0.2.{i}"}
        assert ask(client, new_visitor(), extra=xff).status_code == 200
    response = ask(client, new_visitor(), extra={"X-Forwarded-For": "192.0.2.99"})
    assert response.status_code == 429
    assert response.json()["detail"] == BUSY


def test_busy_message_does_not_mention_other_users(client, monkeypatch):
    import config

    monkeypatch.setattr(config, "ASK_LIMIT_TOTAL", 1)
    ask(client, new_visitor())
    detail = ask(client, new_visitor()).json()["detail"].lower()
    for word in ("other", "user", "visitor", "everyone", "address", "ip"):
        assert word not in detail.split()


def test_state_is_cleared_on_restart(data_dir, clock):
    import api
    from fastapi.testclient import TestClient

    v = new_visitor()
    with TestClient(api.app) as first:
        for _ in range(20):
            ask(first, v)
        assert ask(first, v).status_code == 429
    with TestClient(api.app) as second:
        assert ask(second, v).status_code == 200


# ---- uploads ----


def test_eleventh_upload_in_an_hour_is_refused(client, data_dir):
    v = new_visitor()
    for i in range(10):
        assert upload(client, v, f"f{i}.pdf", make_pdf([f"text {i}"])).status_code == 200
        doc_id = client.get("/documents", headers=headers(v)).json()["documents"][0]["id"]
        client.delete(f"/documents/{doc_id}", headers=headers(v))

    response = upload(client, v, "extra.pdf", make_pdf(["more text"]))
    assert response.status_code == 429
    assert "10 uploads per hour" in response.json()["detail"]
    assert int(response.headers["Retry-After"]) > 0
    assert client.get("/documents", headers=headers(v)).json()["documents"] == []
    assert not [p for p in (data_dir / "documents").rglob("*") if p.is_file()]


def test_rejected_uploads_cost_nothing(client):
    v = new_visitor()
    for _ in range(15):
        assert upload(client, v, "bad.pdf", b"not a pdf").status_code == 400
        assert upload(client, v, "bad.txt", b"x").status_code == 400
    assert upload(client, v, "good.pdf", make_pdf(["fine"])).status_code == 200


def test_one_unit_per_request_even_with_several_files(client):
    v = new_visitor()
    files = [("files", (f"f{i}.pdf", make_pdf([f"t{i}"]), "application/pdf")) for i in range(3)]
    for _ in range(1):
        assert client.post("/upload", files=files, headers=headers(v)).status_code == 200
    used = 1
    # 9 more single-file requests are allowed in the same hour, the 10th fails.
    for i in range(9):
        doc = client.get("/documents", headers=headers(v)).json()["documents"][0]["id"]
        client.delete(f"/documents/{doc}", headers=headers(v))
        assert upload(client, v, f"g{i}.pdf", make_pdf([f"u{i}"])).status_code == 200
        used += 1
    doc = client.get("/documents", headers=headers(v)).json()["documents"][0]["id"]
    client.delete(f"/documents/{doc}", headers=headers(v))
    assert used == 10
    assert upload(client, v, "last.pdf", make_pdf(["late"])).status_code == 429


def test_upload_per_address_and_total_limits(client, monkeypatch):
    import config

    monkeypatch.setattr(config, "UPLOAD_LIMIT_PER_IP", 2)
    monkeypatch.setattr(config, "UPLOAD_LIMIT_TOTAL", 3)
    same = {"X-Forwarded-For": "x, 203.0.113.5"}

    def up(visitor, name, xff):
        return client.post(
            "/upload",
            files=[("files", (name, make_pdf([name]), "application/pdf"))],
            headers={**headers(visitor), **xff},
        )

    assert up(new_visitor(), "a.pdf", same).status_code == 200
    assert up(new_visitor(), "b.pdf", same).status_code == 200
    blocked = up(new_visitor(), "c.pdf", same)
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == BUSY

    assert up(new_visitor(), "d.pdf", {"X-Forwarded-For": "198.51.100.1"}).status_code == 200
    over_total = up(new_visitor(), "e.pdf", {"X-Forwarded-For": "198.51.100.2"})
    assert over_total.status_code == 429
    assert over_total.json()["detail"] == BUSY


def test_client_ip_uses_last_entry_and_falls_back():
    import rate_limit

    class Req:
        def __init__(self, xff, host):
            self.headers = {} if xff is None else {"x-forwarded-for": xff}
            self.client = None if host is None else type("C", (), {"host": host})()

    assert rate_limit.client_ip(Req("1.1.1.1, 2.2.2.2", "9.9.9.9")) == "2.2.2.2"
    assert rate_limit.client_ip(Req("3.3.3.3", "9.9.9.9")) == "3.3.3.3"
    assert rate_limit.client_ip(Req("1.1.1.1, ", "9.9.9.9")) == "1.1.1.1"
    assert rate_limit.client_ip(Req(None, "9.9.9.9")) == "9.9.9.9"
    assert rate_limit.client_ip(Req("", "9.9.9.9")) == "9.9.9.9"
    assert rate_limit.client_ip(Req(None, None)) == "unknown"
