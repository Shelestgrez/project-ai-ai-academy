def test_index_returns_200(client):
    response = client.get("/?lang=ru")
    assert response.status_code == 200
    assert "AI Academy".encode() in response.data or "Academy".encode() in response.data


def test_register_login_logout_flow(client):
    register = client.post(
        "/register?lang=ru",
        data={
            "name": "Anna",
            "email": "anna@academy.test",
            "password": "anna-pass",
        },
        follow_redirects=False,
    )
    assert register.status_code in (302, 303)

    login = client.post(
        "/login?lang=ru",
        data={"email": "anna@academy.test", "password": "anna-pass"},
        follow_redirects=False,
    )
    assert login.status_code in (302, 303)
    assert login.headers["Location"].endswith("/dashboard") or "dashboard" in login.headers["Location"]

    dashboard = client.get("/dashboard?lang=ru")
    assert dashboard.status_code == 200

    logout = client.get("/logout?lang=ru", follow_redirects=False)
    assert logout.status_code in (302, 303)

    blocked = client.get("/dashboard?lang=ru", follow_redirects=False)
    assert blocked.status_code in (302, 303)


def test_duplicate_register_shows_message(client):
    payload = {
        "name": "Bob",
        "email": "bob@academy.test",
        "password": "bob-pass",
    }
    client.post("/register?lang=ru", data=payload)
    again = client.post("/register?lang=ru", data=payload)
    assert again.status_code == 200
    assert "уже существует".encode() in again.data or "already exists".encode() in again.data


def test_login_invalid_credentials(client):
    client.post(
        "/register?lang=ru",
        data={
            "name": "Carl",
            "email": "carl@academy.test",
            "password": "carl-pass",
        },
    )
    bad = client.post(
        "/login?lang=ru",
        data={"email": "carl@academy.test", "password": "wrong"},
    )
    assert bad.status_code == 200
    assert "Неверный".encode() in bad.data or "Invalid".encode() in bad.data
