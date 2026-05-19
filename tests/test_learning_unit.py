from learning import (
    apply_lesson_meta,
    compute_achievements,
    level_from_xp,
    next_lesson_id,
    xp_to_next_level,
)


def test_level_from_xp():
    assert level_from_xp(0) == 1
    assert level_from_xp(499) == 1
    assert level_from_xp(500) == 2
    assert level_from_xp(1200) == 3


def test_xp_to_next_level():
    assert xp_to_next_level(0) == 500
    assert xp_to_next_level(450) == 50


def test_apply_lesson_meta():
    lesson = {"id": "intro-ai", "title": "Test"}
    apply_lesson_meta(lesson)
    assert lesson["level"] == "beginner"
    assert lesson["minutes"] == 15
    assert lesson["xp_reward"] == 100


def test_compute_achievements_empty():
    earned = compute_achievements(0, 9, 0, 0, {}, 0)
    assert earned == []


def test_compute_achievements_first_step():
    earned = compute_achievements(1, 9, 10, 1, {"intro-ai": {"quiz_score": 1, "total_questions": 2}}, 0)
    ids = {item["id"] for item in earned}
    assert "first_step" in ids


def test_next_lesson_id():
    lessons = [
        {"id": "a", "completed": True},
        {"id": "b", "completed": False},
        {"id": "c", "completed": False},
    ]
    assert next_lesson_id(lessons) == "b"
    assert next_lesson_id([{"id": "a", "completed": True}]) is None
