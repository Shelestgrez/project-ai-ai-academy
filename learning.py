from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

LESSON_META: Dict[str, Dict[str, object]] = {
    "intro-ai": {"level": "beginner", "minutes": 15, "xp": 100, "track": "fundamentals"},
    "ml-basics": {"level": "beginner", "minutes": 20, "xp": 120, "track": "fundamentals"},
    "neural-basics": {"level": "intermediate", "minutes": 25, "xp": 140, "track": "fundamentals"},
    "data-foundations": {"level": "beginner", "minutes": 18, "xp": 110, "track": "fundamentals"},
    "ethics-safety": {"level": "beginner", "minutes": 16, "xp": 100, "track": "practice"},
    "gen-ai-llm": {"level": "intermediate", "minutes": 22, "xp": 150, "track": "advanced"},
    "computer-vision": {"level": "intermediate", "minutes": 20, "xp": 130, "track": "advanced"},
    "nlp-basics": {"level": "intermediate", "minutes": 20, "xp": 130, "track": "advanced"},
    "ai-product": {"level": "beginner", "minutes": 17, "xp": 110, "track": "practice"},
}

ACHIEVEMENT_DEFS = [
    {"id": "first_step", "icon": "🎯", "xp": 0},
    {"id": "quiz_ace", "icon": "🏆", "xp": 0},
    {"id": "half_way", "icon": "📈", "xp": 0},
    {"id": "graduate", "icon": "🎓", "xp": 0},
    {"id": "xp_500", "icon": "⚡", "xp": 500},
    {"id": "streak_3", "icon": "🔥", "xp": 0},
    {"id": "collector", "icon": "⭐", "xp": 0},
]


def apply_lesson_meta(lesson: Dict[str, object]) -> None:
    meta = LESSON_META.get(str(lesson["id"]), {})
    lesson["level"] = meta.get("level", "beginner")
    lesson["minutes"] = meta.get("minutes", 15)
    lesson["xp_reward"] = meta.get("xp", 100)
    lesson["track"] = meta.get("track", "fundamentals")


def level_from_xp(xp: int) -> int:
    return max(1, 1 + xp // 500)


def xp_to_next_level(xp: int) -> int:
    current_level = level_from_xp(xp)
    return current_level * 500 - xp


def ensure_user_stats(db, user_id: int) -> Dict[str, Any]:
    row = db.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    db.execute(
        "INSERT INTO user_stats (user_id, xp, streak_days, last_activity_date) VALUES (?, 0, 0, NULL)",
        (user_id,),
    )
    db.commit()
    return {"user_id": user_id, "xp": 0, "streak_days": 0, "last_activity_date": None}


def touch_streak(db, user_id: int) -> Dict[str, Any]:
    stats = ensure_user_stats(db, user_id)
    today = date.today().isoformat()
    last = stats.get("last_activity_date")
    streak = int(stats.get("streak_days") or 0)

    if last == today:
        return stats
    if last:
        try:
            delta = date.today() - date.fromisoformat(str(last))
            if delta.days == 1:
                streak += 1
            elif delta.days > 1:
                streak = 1
        except ValueError:
            streak = 1
    else:
        streak = 1

    db.execute(
        """
        UPDATE user_stats
        SET streak_days = ?, last_activity_date = ?
        WHERE user_id = ?
        """,
        (streak, today, user_id),
    )
    db.commit()
    stats["streak_days"] = streak
    stats["last_activity_date"] = today
    return stats


def add_xp(db, user_id: int, amount: int) -> int:
    if amount <= 0:
        stats = ensure_user_stats(db, user_id)
        return int(stats.get("xp") or 0)
    ensure_user_stats(db, user_id)
    db.execute(
        "UPDATE user_stats SET xp = xp + ? WHERE user_id = ?",
        (amount, user_id),
    )
    db.commit()
    row = db.execute("SELECT xp FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
    return int(row["xp"]) if row else 0


def get_bookmarks(db, user_id: int) -> set:
    rows = db.execute(
        "SELECT lesson_id FROM bookmarks WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return {row["lesson_id"] for row in rows}


def toggle_bookmark(db, user_id: int, lesson_id: str) -> bool:
    existing = db.execute(
        "SELECT 1 FROM bookmarks WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
    ).fetchone()
    if existing:
        db.execute(
            "DELETE FROM bookmarks WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        )
        db.commit()
        return False
    db.execute(
        "INSERT INTO bookmarks (user_id, lesson_id) VALUES (?, ?)",
        (user_id, lesson_id),
    )
    db.commit()
    return True


def get_note(db, user_id: int, lesson_id: str) -> str:
    row = db.execute(
        "SELECT content FROM lesson_notes WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
    ).fetchone()
    return str(row["content"]) if row else ""


def save_note(db, user_id: int, lesson_id: str, content: str) -> None:
    db.execute(
        """
        INSERT INTO lesson_notes (user_id, lesson_id, content)
        VALUES (?, ?, ?)
        ON CONFLICT (user_id, lesson_id) DO UPDATE SET
            content = excluded.content,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, lesson_id, content[:4000]),
    )
    db.commit()


def compute_achievements(
    completed_count: int,
    total_lessons: int,
    xp: int,
    streak: int,
    progress_map: Dict[str, object],
    bookmark_count: int,
) -> List[Dict[str, object]]:
    perfect = any(
        row
        and int(row["total_questions"] or 0) > 0
        and int(row["quiz_score"] or 0) == int(row["total_questions"])
        for row in progress_map.values()
    )
    earned: List[Dict[str, object]] = []
    checks = [
        ("first_step", completed_count >= 1),
        ("quiz_ace", perfect),
        ("half_way", total_lessons > 0 and completed_count >= total_lessons // 2),
        ("graduate", total_lessons > 0 and completed_count >= total_lessons),
        ("xp_500", xp >= 500),
        ("streak_3", streak >= 3),
        ("collector", bookmark_count >= 3),
    ]
    for ach_id, ok in checks:
        if ok:
            meta = next((a for a in ACHIEVEMENT_DEFS if a["id"] == ach_id), {})
            earned.append({"id": ach_id, "icon": meta.get("icon", "✓")})
    return earned


def next_lesson_id(lessons: List[Dict[str, object]]) -> Optional[str]:
    for lesson in lessons:
        if not lesson.get("completed"):
            return str(lesson["id"])
    return None
