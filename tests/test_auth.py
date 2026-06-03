def _register(client, name="Alice", email="alice@example.com", password="pw"):
    return client.post(
        "/api/register",
        json={"name": name, "email": email, "password": password},
    )


def test_register_success(client):
    res = _register(client)
    assert res.status_code == 200
    body = res.get_json()
    assert body["message"]
    assert "id" in body


def test_register_missing_fields(client):
    res = client.post("/api/register", json={"email": "x@y.z"})
    assert res.status_code == 400


def test_register_duplicate_email(client):
    _register(client)
    res = _register(client)
    assert res.status_code == 400


def test_login_success(client):
    _register(client)
    res = client.post(
        "/api/login",
        json={"email": "alice@example.com", "password": "pw"},
    )
    assert res.status_code == 200
    assert res.get_json()["name"] == "Alice"


def test_login_wrong_password(client):
    _register(client)
    res = client.post(
        "/api/login",
        json={"email": "alice@example.com", "password": "wrong"},
    )
    assert res.status_code == 401


def test_profile_requires_auth(client):
    res = client.get("/api/profile")
    assert res.status_code == 401


def test_login_then_profile(client):
    _register(client)
    client.post(
        "/api/login",
        json={"email": "alice@example.com", "password": "pw"},
    )
    res = client.get("/api/profile")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Alice"
