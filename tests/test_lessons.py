def test_dashboard_requires_login(client):
    response = client.get("/dashboard?lang=ru", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "login" in response.headers["Location"]


def test_dashboard_lists_lessons(auth_client):
    response = auth_client.get("/dashboard?lang=ru")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Введение в ИИ" in html or "Introduction to AI" in html
    assert "data-lesson-card" in html
    assert "Опыт" in html or "XP" in html


def test_lesson_page_and_quiz(auth_client):
    lesson = auth_client.get("/lesson/intro-ai?lang=ru")
    assert lesson.status_code == 200
    assert "flashcard" in lesson.data.decode("utf-8")

    quiz = auth_client.post(
        "/quiz/intro-ai?lang=ru",
        data={"q1": "1", "q2": "1", "q3": "0", "q4": "1", "q5": "0"},
        follow_redirects=True,
    )
    assert quiz.status_code == 200
    body = quiz.data.decode("utf-8")
    assert "5/5" in body or "xp_gain" in quiz.request.path or "Получено XP" in body


def test_complete_lesson(auth_client):
    response = auth_client.post(
        "/complete/ml-basics?lang=ru",
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    dashboard = auth_client.get("/dashboard?lang=ru")
    assert dashboard.status_code == 200


def test_unknown_lesson_redirects(auth_client):
    response = auth_client.get("/lesson/unknown-lesson?lang=ru", follow_redirects=False)
    assert response.status_code in (302, 303)


def test_static_lesson_image(auth_client):
    response = auth_client.get("/static/images/intro-ai.jpg")
    assert response.status_code == 200
    assert response.mimetype in ("image/jpeg", "image/jpg")
