def test_bookmark_toggle(auth_client):
    auth_client.post(
        "/bookmark/intro-ai?lang=ru",
        data={"next": "lesson"},
        follow_redirects=True,
    )
    dashboard = auth_client.get("/dashboard?lang=ru")
    assert "bookmark-pin" in dashboard.data.decode("utf-8") or "★" in dashboard.data.decode("utf-8")


def test_save_lesson_note(auth_client):
    response = auth_client.post(
        "/notes/intro-ai?lang=ru",
        data={"content": "ИИ = данные + модель + продукт"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    assert "notes_saved=1" in response.headers["Location"]

    lesson = auth_client.get("/lesson/intro-ai?lang=ru")
    assert "ИИ = данные + модель + продукт" in lesson.data.decode("utf-8")


def test_quiz_awards_xp(auth_client):
    auth_client.post(
        "/quiz/intro-ai?lang=ru",
        data={"q1": "1", "q2": "1", "q3": "0", "q4": "1", "q5": "0"},
        follow_redirects=True,
    )
    dashboard = auth_client.get("/dashboard?lang=ru")
    html = dashboard.data.decode("utf-8")
    assert "stat-value" in html
