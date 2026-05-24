from __future__ import annotations

import os
import random
from functools import wraps
from pathlib import Path
from typing import Dict, List

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db_support import INTEGRITY_ERRORS, attach_database, get_db, init_schema
from learning import (
    add_xp,
    apply_lesson_meta,
    compute_achievements,
    ensure_user_stats,
    get_bookmarks,
    get_note,
    level_from_xp,
    next_lesson_id,
    save_note,
    toggle_bookmark,
    touch_streak,
    xp_to_next_level,
)


BASE_DIR = Path(__file__).resolve().parent


def database_path() -> Path:
    return Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "database.db")))


def create_app() -> Flask:
    db_path = database_path()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["DATABASE"] = str(db_path)
    cookie_secure = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    app.config.update(
        SESSION_COOKIE_SECURE=cookie_secure,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    attach_database(app, str(db_path))

    translations = {
        "ru": {
            "app_title": "AI Academy",
            "tagline": "Изучайте основы искусственного интеллекта с нуля",
            "nav_home": "Главная",
            "nav_register": "Регистрация",
            "nav_login": "Вход",
            "nav_dashboard": "Кабинет",
            "nav_logout": "Выйти",
            "hero_title": "Понимайте ИИ простыми словами",
            "hero_subtitle": "Короткие уроки, практика и персональный прогресс.",
            "cta_start": "Начать обучение",
            "topics_title": "Что вы изучите",
            "topic_1_title": "Что такое ИИ",
            "topic_1_desc": "Базовые определения, виды ИИ и реальные примеры.",
            "topic_2_title": "Машинное обучение",
            "topic_2_desc": "Как модели учатся на данных и почему это работает.",
            "topic_3_title": "Нейронные сети",
            "topic_3_desc": "Как устроены слои, веса и предсказания.",
            "topic_4_title": "Этика ИИ",
            "topic_4_desc": "Справедливость, конфиденциальность и ответственность.",
            "register_title": "Создать аккаунт",
            "register_name": "Имя",
            "register_email": "Email",
            "register_password": "Пароль",
            "register_submit": "Зарегистрироваться",
            "login_title": "Войти",
            "login_submit": "Войти",
            "dashboard_title": "Ваш учебный кабинет",
            "welcome": "Добро пожаловать",
            "progress": "Ваш прогресс",
            "lessons_title": "Уроки",
            "complete_lesson": "Отметить как изучено",
            "open_lesson": "Открыть урок",
            "lesson_title": "Интерактивный урок",
            "lesson_steps": "Ключевые шаги",
            "lesson_overview": "Обзор урока",
            "lesson_sections": "Подробные блоки",
            "practice_title": "Практическое задание",
            "glossary_title": "Мини-словарь",
            "quiz_title": "Проверьте себя",
            "quiz_submit": "Проверить ответы",
            "quiz_result": "Результат",
            "quiz_feedback_good": "Отлично! Можно двигаться дальше.",
            "quiz_feedback_retry": "Неплохо, повторите материал и попробуйте снова.",
            "back_dashboard": "Вернуться в кабинет",
            "score_label": "Баллы",
            "status_done": "Изучено",
            "status_pending": "Не изучено",
            "message_register_success": "Регистрация прошла успешно. Теперь войдите.",
            "message_user_exists": "Пользователь с таким email уже существует.",
            "message_login_error": "Неверный email или пароль.",
            "not_found": "Урок не найден.",
            "stats_xp": "Опыт",
            "stats_level": "Уровень",
            "stats_streak": "Серия дней",
            "stats_achievements": "Достижения",
            "minutes_label": "мин",
            "level_beginner": "Начальный",
            "level_intermediate": "Средний",
            "track_fundamentals": "Основы",
            "track_advanced": "Продвинутый",
            "track_practice": "Практика",
            "search_lessons": "Поиск урока...",
            "filter_all": "Все",
            "filter_done": "Пройденные",
            "filter_pending": "В процессе",
            "filter_bookmarked": "Закладки",
            "continue_learning": "Продолжить обучение",
            "continue_cta": "Открыть следующий урок",
            "bookmark": "В закладки",
            "bookmarked": "В закладках",
            "notes_title": "Мои заметки",
            "notes_placeholder": "Запишите главное из урока...",
            "notes_save": "Сохранить заметку",
            "notes_saved": "Заметка сохранена",
            "flashcards_title": "Карточки терминов",
            "flashcards_hint": "Нажмите на карточку, чтобы увидеть определение",
            "steps_check_title": "Чек-лист шагов",
            "daily_challenge": "Вопрос дня",
            "tab_content": "Урок",
            "tab_cards": "Карточки",
            "tab_notes": "Заметки",
            "dark_mode": "Тёмная тема",
            "light_mode": "Светлая тема",
            "ach_first_step": "Первый шаг",
            "ach_quiz_ace": "Идеальный тест",
            "ach_half_way": "Полпути",
            "ach_graduate": "Выпускник",
            "ach_xp_500": "500 XP",
            "ach_streak_3": "Серия 3 дня",
            "ach_collector": "Коллекционер",
            "xp_gained": "Получено XP",
            "all_lessons_done": "Все уроки пройдены — отличная работа!",
            "daily_ok": "Верно! Так держать.",
            "daily_fail": "Неверно. Откройте урок и повторите тему.",
        },
        "en": {
            "app_title": "AI Academy",
            "tagline": "Learn the fundamentals of artificial intelligence from scratch",
            "nav_home": "Home",
            "nav_register": "Register",
            "nav_login": "Login",
            "nav_dashboard": "Dashboard",
            "nav_logout": "Logout",
            "hero_title": "Understand AI in simple terms",
            "hero_subtitle": "Short lessons, practice, and personal progress.",
            "cta_start": "Start learning",
            "topics_title": "What you will learn",
            "topic_1_title": "What AI is",
            "topic_1_desc": "Core definitions, AI types, and real examples.",
            "topic_2_title": "Machine learning",
            "topic_2_desc": "How models learn from data and why it works.",
            "topic_3_title": "Neural networks",
            "topic_3_desc": "How layers, weights, and predictions work.",
            "topic_4_title": "AI ethics",
            "topic_4_desc": "Fairness, privacy, and responsibility.",
            "register_title": "Create account",
            "register_name": "Name",
            "register_email": "Email",
            "register_password": "Password",
            "register_submit": "Sign up",
            "login_title": "Sign in",
            "login_submit": "Sign in",
            "dashboard_title": "Your learning dashboard",
            "welcome": "Welcome",
            "progress": "Your progress",
            "lessons_title": "Lessons",
            "complete_lesson": "Mark as completed",
            "open_lesson": "Open lesson",
            "lesson_title": "Interactive lesson",
            "lesson_steps": "Key steps",
            "lesson_overview": "Lesson overview",
            "lesson_sections": "Detailed modules",
            "practice_title": "Practice task",
            "glossary_title": "Mini glossary",
            "quiz_title": "Check yourself",
            "quiz_submit": "Check answers",
            "quiz_result": "Result",
            "quiz_feedback_good": "Great work! You can move on.",
            "quiz_feedback_retry": "Good start. Review the lesson and try again.",
            "back_dashboard": "Back to dashboard",
            "score_label": "Score",
            "status_done": "Completed",
            "status_pending": "Not completed",
            "message_register_success": "Registration successful. Please sign in.",
            "message_user_exists": "A user with this email already exists.",
            "message_login_error": "Invalid email or password.",
            "not_found": "Lesson not found.",
            "stats_xp": "XP",
            "stats_level": "Level",
            "stats_streak": "Day streak",
            "stats_achievements": "Achievements",
            "minutes_label": "min",
            "level_beginner": "Beginner",
            "level_intermediate": "Intermediate",
            "track_fundamentals": "Fundamentals",
            "track_advanced": "Advanced",
            "track_practice": "Practice",
            "search_lessons": "Search lessons...",
            "filter_all": "All",
            "filter_done": "Completed",
            "filter_pending": "In progress",
            "filter_bookmarked": "Bookmarks",
            "continue_learning": "Continue learning",
            "continue_cta": "Open next lesson",
            "bookmark": "Bookmark",
            "bookmarked": "Bookmarked",
            "notes_title": "My notes",
            "notes_placeholder": "Write your key takeaways...",
            "notes_save": "Save note",
            "notes_saved": "Note saved",
            "flashcards_title": "Term flashcards",
            "flashcards_hint": "Tap a card to reveal the definition",
            "steps_check_title": "Step checklist",
            "daily_challenge": "Daily challenge",
            "tab_content": "Lesson",
            "tab_cards": "Cards",
            "tab_notes": "Notes",
            "dark_mode": "Dark mode",
            "light_mode": "Light mode",
            "ach_first_step": "First step",
            "ach_quiz_ace": "Quiz ace",
            "ach_half_way": "Halfway",
            "ach_graduate": "Graduate",
            "ach_xp_500": "500 XP",
            "ach_streak_3": "3-day streak",
            "ach_collector": "Collector",
            "xp_gained": "XP earned",
            "all_lessons_done": "All lessons completed — great job!",
            "daily_ok": "Correct! Keep going.",
            "daily_fail": "Not quite. Review the lesson and try again.",
        },
        "kk": {
            "app_title": "AI Academy",
            "tagline": "Жасанды интеллект негіздерін нөлден үйреніңіз",
            "nav_home": "Басты бет",
            "nav_register": "Тіркелу",
            "nav_login": "Кіру",
            "nav_dashboard": "Кабинет",
            "nav_logout": "Шығу",
            "hero_title": "ЖИ-ді қарапайым тілмен түсініңіз",
            "hero_subtitle": "Қысқа сабақтар, тәжірибе және жеке прогресс.",
            "cta_start": "Оқуды бастау",
            "topics_title": "Нені үйренесіз",
            "topic_1_title": "ЖИ деген не",
            "topic_1_desc": "Негізгі анықтамалар, ЖИ түрлері және мысалдар.",
            "topic_2_title": "Машиналық оқыту",
            "topic_2_desc": "Модельдер деректерден қалай үйренеді.",
            "topic_3_title": "Нейрондық желілер",
            "topic_3_desc": "Қабаттар, салмақтар және болжамдар қалай жұмыс істейді.",
            "topic_4_title": "ЖИ этикасы",
            "topic_4_desc": "Әділеттілік, құпиялылық және жауапкершілік.",
            "register_title": "Аккаунт жасау",
            "register_name": "Аты",
            "register_email": "Email",
            "register_password": "Құпиясөз",
            "register_submit": "Тіркелу",
            "login_title": "Кіру",
            "login_submit": "Кіру",
            "dashboard_title": "Сіздің оқу кабинетіңіз",
            "welcome": "Қош келдіңіз",
            "progress": "Сіздің прогрессіңіз",
            "lessons_title": "Сабақтар",
            "complete_lesson": "Оқылды деп белгілеу",
            "open_lesson": "Сабақты ашу",
            "lesson_title": "Интерактивті сабақ",
            "lesson_steps": "Негізгі қадамдар",
            "lesson_overview": "Сабаққа шолу",
            "lesson_sections": "Толық модульдер",
            "practice_title": "Тәжірибелік тапсырма",
            "glossary_title": "Шағын сөздік",
            "quiz_title": "Өзіңізді тексеріңіз",
            "quiz_submit": "Жауаптарды тексеру",
            "quiz_result": "Нәтиже",
            "quiz_feedback_good": "Тамаша! Келесіге өте аласыз.",
            "quiz_feedback_retry": "Жақсы бастама. Материалды қайталап көріңіз.",
            "back_dashboard": "Кабинетке оралу",
            "score_label": "Ұпай",
            "status_done": "Оқылды",
            "status_pending": "Оқылмады",
            "message_register_success": "Тіркелу сәтті өтті. Енді кіріңіз.",
            "message_user_exists": "Бұл email-пен қолданушы бар.",
            "message_login_error": "Email немесе құпиясөз қате.",
            "not_found": "Сабақ табылмады.",
            "stats_xp": "Тәжірибе",
            "stats_level": "Деңгей",
            "stats_streak": "Күн сериясы",
            "stats_achievements": "Жетістіктер",
            "minutes_label": "мин",
            "level_beginner": "Бастапқы",
            "level_intermediate": "Орта",
            "track_fundamentals": "Негіздер",
            "track_advanced": "Күрделі",
            "track_practice": "Тәжірибе",
            "search_lessons": "Сабақ іздеу...",
            "filter_all": "Барлығы",
            "filter_done": "Өтілген",
            "filter_pending": "Процесте",
            "filter_bookmarked": "Бетбелгілер",
            "continue_learning": "Оқуды жалғастыру",
            "continue_cta": "Келесі сабақ",
            "bookmark": "Бетбелгі",
            "bookmarked": "Сақталды",
            "notes_title": "Жазбаларым",
            "notes_placeholder": "Негізгі ойларыңызды жазыңыз...",
            "notes_save": "Сақтау",
            "notes_saved": "Сақталды",
            "flashcards_title": "Термин карточкалары",
            "flashcards_hint": "Анықтаманы көру үшін басыңыз",
            "steps_check_title": "Қадам тізімі",
            "daily_challenge": "Күн сұрағы",
            "tab_content": "Сабақ",
            "tab_cards": "Карточкалар",
            "tab_notes": "Жазбалар",
            "dark_mode": "Қараңғы тема",
            "light_mode": "Жарық тема",
            "ach_first_step": "Бірінші қадам",
            "ach_quiz_ace": "Тамаша тест",
            "ach_half_way": "Жарты жол",
            "ach_graduate": "Түлек",
            "ach_xp_500": "500 XP",
            "ach_streak_3": "3 күн сериясы",
            "ach_collector": "Жинақтаушы",
            "xp_gained": "XP алынды",
            "all_lessons_done": "Барлық сабақ өтілді!",
            "daily_ok": "Дұрыс! Жалғастырыңыз.",
            "daily_fail": "Қате. Сабақты қайталаңыз.",
        },
    }

    achievement_labels = {
        "ru": {
            "first_step": "ach_first_step",
            "quiz_ace": "ach_quiz_ace",
            "half_way": "ach_half_way",
            "graduate": "ach_graduate",
            "xp_500": "ach_xp_500",
            "streak_3": "ach_streak_3",
            "collector": "ach_collector",
        },
        "en": {
            "first_step": "ach_first_step",
            "quiz_ace": "ach_quiz_ace",
            "half_way": "ach_half_way",
            "graduate": "ach_graduate",
            "xp_500": "ach_xp_500",
            "streak_3": "ach_streak_3",
            "collector": "ach_collector",
        },
        "kk": {
            "first_step": "ach_first_step",
            "quiz_ace": "ach_quiz_ace",
            "half_way": "ach_half_way",
            "graduate": "ach_graduate",
            "xp_500": "ach_xp_500",
            "streak_3": "ach_streak_3",
            "collector": "ach_collector",
        },
    }

    lesson_catalog: Dict[str, List[Dict[str, object]]] = {
        "ru": [
            {
                "id": "intro-ai",
                "title": "Введение в ИИ",
                "description": "Что такое искусственный интеллект и где он применяется.",
                "steps": [
                    "ИИ - это системы, которые выполняют интеллектуальные задачи.",
                    "Сильный и слабый ИИ различаются по уровню универсальности.",
                    "Сегодня ИИ используется в медицине, финансах, образовании и транспорте.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Что лучше описывает современный ИИ?",
                        "options": [
                            "Универсальный человеческий разум",
                            "Система для конкретных задач",
                            "Только робот в физическом теле",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Где ИИ применяется уже сейчас?",
                        "options": [
                            "Только в научной фантастике",
                            "Только в играх",
                            "В медицине и финансах",
                        ],
                        "answer": 2,
                    },
                ],
            },
            {
                "id": "ml-basics",
                "title": "Основы машинного обучения",
                "description": "Обучение с учителем, без учителя и переобучение.",
                "steps": [
                    "Модель обучается на примерах и ищет закономерности.",
                    "Обучение с учителем использует размеченные данные.",
                    "Переобучение возникает, когда модель запоминает, но плохо обобщает.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Что нужно для обучения с учителем?",
                        "options": [
                            "Только неразмеченные данные",
                            "Размеченные примеры с правильными ответами",
                            "Вообще без данных",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Что такое переобучение?",
                        "options": [
                            "Модель хорошо запомнила тренировочные данные, но плохо работает на новых",
                            "Модель не обучалась совсем",
                            "Модель работает быстрее",
                        ],
                        "answer": 0,
                    },
                ],
            },
            {
                "id": "neural-basics",
                "title": "Нейронные сети",
                "description": "Перцептрон, функции активации и обратное распространение.",
                "steps": [
                    "Нейронная сеть состоит из входного, скрытых и выходного слоев.",
                    "Весы определяют вклад каждого признака в итоговый прогноз.",
                    "Backpropagation корректирует веса, уменьшая ошибку.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Для чего нужны веса в сети?",
                        "options": [
                            "Чтобы отключать интернет",
                            "Чтобы оценивать важность входных признаков",
                            "Чтобы хранить картинки",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Что делает backpropagation?",
                        "options": [
                            "Случайно меняет параметры",
                            "Обновляет веса для снижения ошибки",
                            "Удаляет данные",
                        ],
                        "answer": 1,
                    },
                ],
            },
        ],
        "en": [
            {
                "id": "intro-ai",
                "title": "Introduction to AI",
                "description": "What artificial intelligence is and where it is used.",
                "steps": [
                    "AI systems perform tasks that normally require human intelligence.",
                    "Narrow AI is built for specific tasks, unlike general intelligence.",
                    "AI is already used in healthcare, finance, education, and transport.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "What best describes current AI?",
                        "options": [
                            "General human-level intelligence",
                            "Task-specific systems",
                            "Only physical robots",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Where is AI actively used today?",
                        "options": [
                            "Only in sci-fi movies",
                            "Only in gaming",
                            "Healthcare and finance",
                        ],
                        "answer": 2,
                    },
                ],
            },
            {
                "id": "ml-basics",
                "title": "Machine Learning Basics",
                "description": "Supervised learning, unsupervised learning, and overfitting.",
                "steps": [
                    "Models learn from examples and identify useful patterns.",
                    "Supervised learning relies on labeled input-output pairs.",
                    "Overfitting means great training accuracy but weak generalization.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "What does supervised learning require?",
                        "options": [
                            "Only unlabeled data",
                            "Labeled examples with expected outputs",
                            "No data at all",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "What is overfitting?",
                        "options": [
                            "Memorizing training data but failing on new data",
                            "Refusing to train the model",
                            "Increasing server speed",
                        ],
                        "answer": 0,
                    },
                ],
            },
            {
                "id": "neural-basics",
                "title": "Neural Networks",
                "description": "Perceptron, activation functions, and backpropagation.",
                "steps": [
                    "Neural networks include input, hidden, and output layers.",
                    "Weights control how much each feature affects predictions.",
                    "Backpropagation updates weights to reduce prediction error.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "What is the role of weights?",
                        "options": [
                            "Disconnect internet access",
                            "Represent feature importance",
                            "Store screenshots",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "What does backpropagation do?",
                        "options": [
                            "Updates weights to minimize error",
                            "Deletes old files",
                            "Randomly changes UI colors",
                        ],
                        "answer": 0,
                    },
                ],
            },
        ],
        "kk": [
            {
                "id": "intro-ai",
                "title": "ЖИ-ге кіріспе",
                "description": "Жасанды интеллект дегеніміз не және қайда қолданылады.",
                "steps": [
                    "ЖИ - адам ақылын қажет ететін міндеттерді орындайтын жүйе.",
                    "Тар ЖИ нақты бір міндетке бағытталған.",
                    "Бүгінде ЖИ медицинада, қаржыда, білімде және көлікте қолданылады.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Қазіргі ЖИ-ді не дұрыс сипаттайды?",
                        "options": [
                            "Адам деңгейіндегі әмбебап интеллект",
                            "Нақты міндетке арналған жүйелер",
                            "Тек роботтар",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "ЖИ қазір қай салада қолданылады?",
                        "options": [
                            "Тек фантастикада",
                            "Тек ойындарда",
                            "Медицина мен қаржыда",
                        ],
                        "answer": 2,
                    },
                ],
            },
            {
                "id": "ml-basics",
                "title": "Машиналық оқыту негіздері",
                "description": "Бақылаулы және бақылаусыз оқыту, артық үйрену.",
                "steps": [
                    "Модель мысалдар арқылы заңдылықтарды үйренеді.",
                    "Бақылаулы оқытуда белгіленген деректер қолданылады.",
                    "Артық үйрену жаңа деректерге бейімделуді нашарлатады.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Бақылаулы оқытуға не керек?",
                        "options": [
                            "Тек белгіленбеген деректер",
                            "Дұрыс жауабы бар белгіленген мысалдар",
                            "Ешқандай дерек қажет емес",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Артық үйрену деген не?",
                        "options": [
                            "Модель жаттығу дерегін жаттап, жаңа деректе нашар жұмыс істеуі",
                            "Модель мүлде оқымауы",
                            "Тек интерфейсті өзгерту",
                        ],
                        "answer": 0,
                    },
                ],
            },
            {
                "id": "neural-basics",
                "title": "Нейрондық желілер",
                "description": "Перцептрон, активация функциялары және backpropagation.",
                "steps": [
                    "Нейрондық желі кіріс, жасырын және шығыс қабаттарынан тұрады.",
                    "Салмақтар әр белгі қасиетінің маңызын анықтайды.",
                    "Backpropagation қателікті азайту үшін салмақтарды жаңартады.",
                ],
                "quiz": [
                    {
                        "id": "q1",
                        "question": "Желідегі салмақ не үшін керек?",
                        "options": [
                            "Интернетті өшіру үшін",
                            "Белгі қасиеттерінің маңызын бағалау үшін",
                            "Файл сақтау үшін",
                        ],
                        "answer": 1,
                    },
                    {
                        "id": "q2",
                        "question": "Backpropagation не істейді?",
                        "options": [
                            "Салмақтарды қателікті азайту үшін жаңартады",
                            "Деректерді жояды",
                            "Экран түсін өзгертеді",
                        ],
                        "answer": 0,
                    },
                ],
            },
        ],
    }

    deep_lessons: Dict[str, Dict[str, Dict[str, object]]] = {
        "ru": {
            "intro-ai": {
                "overview": "Этот урок формирует системное понимание ИИ: от определений и классов задач до ограничений, командной работы и жизненного цикла внедрения в продукт.",
                "sections": [
                    {
                        "title": "1) ИИ как инженерная система",
                        "text": "Современный ИИ — это не магия и не один алгоритм, а связка данных, модели, инфраструктуры и продукта. Успех зависит от качества данных, метрик и итераций с пользователями.",
                        "image": "images/sections/pipeline.jpg",
                    },
                    {
                        "title": "2) Классы задач",
                        "text": "Основные классы: классификация, регрессия, кластеризация, генерация контента, рекомендации и поиск аномалий. Для каждой задачи выбирают свой набор метрик и способ проверки.",
                    },
                    {
                        "title": "3) Слабый и сильный ИИ",
                        "text": "Слабый (узкий) ИИ решает конкретные задачи — распознавание речи, рекомендации, диагностика. Сильный ИИ — гипотетическая универсальная система; на практике сегодня применяют именно узкие решения.",
                    },
                    {
                        "title": "4) Ограничения и риски",
                        "text": "ИИ ошибается из-за смещённых данных, плохой разметки или смены среды (data drift). Нужны мониторинг качества, человеческий контроль и понятные процедуры эскалации.",
                    },
                    {
                        "title": "5) Жизненный цикл внедрения",
                        "text": "Типичный цикл: постановка задачи → сбор данных → baseline → эксперименты → валидация → пилот → мониторинг в продакшене. Каждый этап имеет свои артефакты и критерии готовности.",
                    },
                ],
                "practice": "Выберите любой сервис (например, музыкальное приложение) и опишите 3 места, где ИИ может улучшить опыт пользователя: входные данные, ожидаемый результат и метрика успеха.",
                "glossary": [
                    {"term": "Датасет", "definition": "Набор данных для обучения и проверки модели."},
                    {"term": "Инференс", "definition": "Применение обученной модели к новым данным."},
                    {"term": "Метрика", "definition": "Числовой показатель качества модели."},
                    {"term": "Baseline", "definition": "Простая модель или правило, с которым сравнивают более сложные решения."},
                    {"term": "Data drift", "definition": "Изменение распределения входных данных со временем."},
                ],
                "steps": [
                    "Определите бизнес-задачу и критерий успеха до выбора модели.",
                    "Проверьте качество и репрезентативность данных перед обучением.",
                    "Сравните простой baseline и более сложные модели по метрикам.",
                    "Проведите тест на новых данных, не использованных при обучении.",
                    "Согласуйте с командой пороги качества для пилота и продакшена.",
                    "Добавьте мониторинг после внедрения для контроля деградации.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Что важнее на старте проекта ИИ?", "options": ["Сразу выбрать сложную нейросеть", "Четко определить задачу и метрику", "Купить более дорогой сервер"], "answer": 1},
                    {"id": "q2", "question": "Что описывает инференс?", "options": ["Разметку датасета", "Применение модели к новым данным", "Удаление выбросов"], "answer": 1},
                    {"id": "q3", "question": "Почему baseline полезен?", "options": ["Показывает минимальный уровень, который нужно превзойти", "Ускоряет интернет", "Устраняет все ошибки данных"], "answer": 0},
                    {"id": "q4", "question": "Какой риск критичен после запуска?", "options": ["Смена цвета интерфейса", "Data drift и падение качества", "Слишком короткое название модели"], "answer": 1},
                    {"id": "q5", "question": "Что характерно для узкого (слабого) ИИ?", "options": ["Решает одну конкретную задачу хорошо", "Мыслит как человек в любой области", "Не требует данных"], "answer": 0},
                ],
            },
            "ml-basics": {
                "overview": "Урок раскрывает полный цикл ML: подготовка данных, выбор модели, валидация, борьба с переобучением и вывод модели в продакшен.",
                "sections": [
                    {
                        "title": "1) Pipeline данных",
                        "text": "Сбор, очистка, кодирование категорий, масштабирование признаков и разделение на train/validation/test без утечки информации.",
                        "image": "images/sections/data-quality.jpg",
                    },
                    {"title": "2) Обучение с учителем и без", "text": "С учителем — есть правильные ответы (классификация, регрессия). Без учителя — ищут структуру (кластеризация, снижение размерности)."},
                    {"title": "3) Выбор алгоритма", "text": "Линейные модели интерпретируемы, деревья и бустинг сильны на табличных данных, нейросети — на изображениях, тексте и сложных признаках."},
                    {"title": "4) Оценка качества", "text": "Не ограничивайтесь accuracy. При дисбалансе классов используйте precision, recall, F1 и матрицу ошибок."},
                    {"title": "5) Регуляризация и переобучение", "text": "L1/L2, ранняя остановка, dropout (для нейросетей) и кросс-валидация помогают модели обобщать, а не запоминать шум."},
                ],
                "practice": "Возьмите задачу прогноза оттока клиентов: опишите целевую переменную, 5 признаков, 2 метрики, способ борьбы с дисбалансом и какой baseline вы бы построили первым.",
                "glossary": [
                    {"term": "Train/Test split", "definition": "Разделение данных для обучения и независимой проверки."},
                    {"term": "Overfitting", "definition": "Переобучение: модель запомнила шум и плохо обобщает."},
                    {"term": "Feature Engineering", "definition": "Создание информативных признаков для модели."},
                    {"term": "Cross-validation", "definition": "Повторное обучение на разных частях данных для оценки устойчивости."},
                    {"term": "Hyperparameter", "definition": "Настройка модели, задаваемая до обучения (глубина дерева, learning rate)."},
                ],
                "steps": [
                    "Подготовьте данные: удалите дубликаты и обработайте пропуски.",
                    "Разделите выборку на train/validation/test без утечки данных.",
                    "Обучите baseline-модель и зафиксируйте метрики.",
                    "Сделайте тюнинг гиперпараметров на validation.",
                    "Сравните несколько алгоритмов по одной и той же метрике.",
                    "Проверьте устойчивость модели на новых батчах данных.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Зачем нужен test set?", "options": ["Для обучения гиперпараметров", "Для независимой финальной проверки", "Чтобы хранить логи"], "answer": 1},
                    {"id": "q2", "question": "Что такое утечка данных?", "options": ["Недостаток памяти", "Использование информации из будущего в обучении", "Плохой Wi-Fi"], "answer": 1},
                    {"id": "q3", "question": "Какая метрика полезна при дисбалансе?", "options": ["Только accuracy", "F1-score", "Только скорость инференса"], "answer": 1},
                    {"id": "q4", "question": "Что обычно снижает переобучение?", "options": ["Больше эпох без контроля", "Регуляризация и валидация", "Удаление test set"], "answer": 1},
                    {"id": "q5", "question": "Где чаще применяют бустинг на деревьях?", "options": ["На табличных бизнес-данных", "Только для генерации музыки", "Только для 3D-анимации"], "answer": 0},
                ],
            },
            "neural-basics": {
                "overview": "Урок объясняет механику нейросетей: слои, активации, функцию потерь, обратное распространение и практики стабильного обучения.",
                "sections": [
                    {
                        "title": "1) Архитектура",
                        "text": "Сеть состоит из слоёв: вход преобразуется в скрытые представления, выход даёт прогноз. Глубина и ширина слоёв — гиперпараметры.",
                        "image": "images/sections/neural-layers.jpg",
                    },
                    {"title": "2) Перцептрон и веса", "text": "Нейрон суммирует входы с весами, добавляет смещение (bias) и пропускает результат через функцию активации."},
                    {"title": "3) Обучение", "text": "Forward pass → loss → backpropagation вычисляет градиенты → оптимизатор (SGD, Adam) обновляет веса. Цикл повторяется по эпохам."},
                    {"title": "4) Функции активации", "text": "ReLU ускоряет обучение, sigmoid/softmax — для вероятностей, GELU часто в трансформерах. Без нелинейности сеть не сложнее линейной модели."},
                    {"title": "5) Стабильность", "text": "Batch normalization, dropout, подбор learning rate и ранняя остановка снижают риск расходимости и переобучения."},
                ],
                "practice": "Опишите архитектуру для распознавания рукописных цифр: вход, 2 скрытых слоя, выход, функцию потерь и метрику.",
                "glossary": [
                    {"term": "Activation Function", "definition": "Нелинейная функция (ReLU, GELU, sigmoid), позволяющая сети учить сложные зависимости."},
                    {"term": "Loss Function", "definition": "Функция ошибки между предсказанием и целевым значением."},
                    {"term": "Gradient", "definition": "Показывает, как изменить параметры для уменьшения ошибки."},
                ],
                "steps": [
                    "Сформируйте входные признаки и нормализуйте значения.",
                    "Выполните forward pass и получите предсказание.",
                    "Посчитайте loss и оцените величину ошибки.",
                    "Через backpropagation вычислите градиенты по слоям.",
                    "Обновите веса оптимизатором (SGD/Adam) и повторите цикл.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Зачем нужна функция активации?", "options": ["Для нелинейности модели", "Только для визуализации", "Для сохранения CSV"], "answer": 0},
                    {"id": "q2", "question": "Что минимизирует оптимизатор?", "options": ["Размер датасета", "Функцию потерь", "Количество слоев"], "answer": 1},
                    {"id": "q3", "question": "Что делает dropout?", "options": ["Отключает случайные нейроны во время обучения", "Удаляет метки классов", "Ускоряет интернет"], "answer": 0},
                    {"id": "q4", "question": "Что может вызвать нестабильное обучение?", "options": ["Слишком большой learning rate", "Четкая валидация", "Нормализация входа"], "answer": 0},
                    {"id": "q5", "question": "Что делает backpropagation?", "options": ["Распространяет градиент ошибки назад по слоям", "Удаляет обучающую выборку", "Меняет язык интерфейса"], "answer": 0},
                ],
            },
        },
        "en": {},
        "kk": {},
    }

    deep_lessons["en"] = {
        "intro-ai": {
            "overview": "This lesson builds structured understanding of AI: definitions, task classes, narrow vs general AI, risks, and deployment lifecycle.",
            "sections": [
                {"title": "1) AI as an engineering system", "text": "Modern AI combines data, models, infrastructure, and product decisions. Data quality and metrics usually matter more than model complexity.", "image": "images/sections/pipeline.jpg"},
                {"title": "2) Task classes", "text": "Core classes include classification, regression, clustering, recommendation, generation, and anomaly detection."},
                {"title": "3) Narrow vs general AI", "text": "Today's production systems are narrow AI: strong at one task. General AI remains a research goal, not a shipped product pattern."},
                {"title": "4) Practical limits", "text": "Models fail when data shifts or labels are noisy. Monitoring, human review, and escalation paths are mandatory."},
                {"title": "5) Deployment lifecycle", "text": "Typical flow: problem framing → data → baseline → experiments → validation → pilot → production monitoring."},
            ],
            "practice": "Pick one app you use daily and describe 3 AI opportunities: required inputs, expected output, and success metric.",
            "glossary": [
                {"term": "Dataset", "definition": "A collection of examples used for training and evaluation."},
                {"term": "Inference", "definition": "Running a trained model on new data."},
                {"term": "Metric", "definition": "A numerical indicator of model quality."},
            ],
            "steps": [
                "Define business objective and measurable success before choosing a model.",
                "Audit data representativeness and label quality.",
                "Start with a simple baseline and compare against stronger models.",
                "Validate on held-out data not used during training.",
                "Monitor post-deployment drift and quality decay.",
            ],
            "quiz": [
                {"id": "q1", "question": "What is the best first step in an AI project?", "options": ["Choose the deepest neural net", "Define objective and metric", "Increase server budget"], "answer": 1},
                {"id": "q2", "question": "What is inference?", "options": ["Labeling data", "Using a trained model on new data", "Removing outliers"], "answer": 1},
                {"id": "q3", "question": "Why use a baseline model?", "options": ["To set a minimum benchmark", "To replace all testing", "To remove data bias automatically"], "answer": 0},
                {"id": "q4", "question": "What is a major post-launch risk?", "options": ["UI color changes", "Data drift", "Model name length"], "answer": 1},
                {"id": "q5", "question": "What describes narrow AI?", "options": ["Strong at a specific task", "Human-level in every domain", "Needs no data"], "answer": 0},
            ],
        },
        "ml-basics": {
            "overview": "This lesson covers the ML workflow: preparation, model choice, validation, overfitting control, and production readiness.",
            "sections": [
                {"title": "1) Data pipeline", "text": "Collect, clean, encode categories, scale features, and split into train/validation/test without leakage.", "image": "images/sections/data-quality.jpg"},
                {"title": "2) Supervised vs unsupervised", "text": "Supervised learning uses labels; unsupervised learning discovers structure such as clusters."},
                {"title": "3) Algorithm selection", "text": "Linear models are interpretable, tree ensembles excel on tabular data, neural nets on images and text."},
                {"title": "4) Evaluation strategy", "text": "Go beyond accuracy. Use precision, recall, F1, and confusion-matrix analysis."},
                {"title": "5) Regularization", "text": "L1/L2, early stopping, and cross-validation help models generalize instead of memorizing noise."},
            ],
            "practice": "For a churn prediction task, define target variable, 5 candidate features, 2 metrics, and one class-imbalance strategy.",
            "glossary": [
                {"term": "Train/Test split", "definition": "Separating data for learning and independent evaluation."},
                {"term": "Overfitting", "definition": "Memorizing training noise and failing on unseen data."},
                {"term": "Feature Engineering", "definition": "Designing informative input variables."},
            ],
            "steps": [
                "Clean missing values and duplicates.",
                "Split data without leakage.",
                "Train a baseline and capture metrics.",
                "Tune hyperparameters with validation.",
                "Stress-test stability on fresh batches.",
            ],
            "quiz": [
                {"id": "q1", "question": "Why do we need a test set?", "options": ["To tune hyperparameters", "For independent final evaluation", "To store logs"], "answer": 1},
                {"id": "q2", "question": "What is data leakage?", "options": ["Low memory", "Using future information during training", "Slow internet"], "answer": 1},
                {"id": "q3", "question": "Which metric is useful for imbalanced classes?", "options": ["Only accuracy", "F1-score", "Only latency"], "answer": 1},
                {"id": "q4", "question": "What usually reduces overfitting?", "options": ["More uncontrolled epochs", "Regularization and validation", "Removing test set"], "answer": 1},
            ],
        },
        "neural-basics": {
            "overview": "This lesson explains how neural networks learn: layers, activations, loss, backpropagation, and training stability.",
            "sections": [
                {"title": "1) Architecture", "text": "Layers transform inputs into hidden representations and final predictions. Depth and width are hyperparameters.", "image": "images/sections/neural-layers.jpg"},
                {"title": "2) Perceptron and weights", "text": "A neuron combines weighted inputs, adds bias, and applies an activation function."},
                {"title": "3) Learning loop", "text": "Forward pass → loss → backpropagation → optimizer update. The cycle repeats for many epochs."},
                {"title": "4) Activation functions", "text": "ReLU speeds training; sigmoid/softmax output probabilities; GELU is common in transformers."},
                {"title": "5) Training stability", "text": "Batch norm, dropout, learning-rate tuning, and early stopping reduce divergence and overfitting."},
            ],
            "practice": "Design a simple network for digit recognition: input, two hidden layers, output size, loss function, and metric.",
            "glossary": [
                {"term": "Activation Function", "definition": "A non-linear function such as ReLU, GELU, or sigmoid."},
                {"term": "Loss Function", "definition": "A function that measures prediction error."},
                {"term": "Gradient", "definition": "A direction signal for reducing the loss."},
            ],
            "steps": [
                "Normalize features and prepare tensors.",
                "Run forward pass to get predictions.",
                "Compute loss against targets.",
                "Backpropagate gradients through layers.",
                "Update weights with Adam/SGD and repeat.",
            ],
            "quiz": [
                {"id": "q1", "question": "Why do we use activation functions?", "options": ["To add non-linearity", "Only for charts", "To store CSV files"], "answer": 0},
                {"id": "q2", "question": "What does the optimizer minimize?", "options": ["Dataset size", "Loss function", "Number of layers"], "answer": 1},
                {"id": "q3", "question": "What does dropout do?", "options": ["Randomly disables neurons during training", "Deletes labels", "Improves network speed"], "answer": 0},
                {"id": "q4", "question": "What can cause unstable training?", "options": ["Too high learning rate", "Input normalization", "Careful validation"], "answer": 0},
            ],
        },
    }
    deep_lessons["kk"] = {
        "intro-ai": {
            "overview": "Бұл сабақ ЖИ туралы жүйелі түсінік береді: анықтама, міндет түрлері, тар/күшті ЖИ, тәуекелдер және енгізу циклі.",
            "sections": [
                {"title": "1) ЖИ инженерлік жүйе ретінде", "text": "Қазіргі ЖИ — деректер, модель, инфрақұрылым және өнім шешімдерінің бірігуі.", "image": "images/sections/pipeline.jpg"},
                {"title": "2) Міндет кластары", "text": "Негізгі класстар: классификация, регрессия, кластерлеу, ұсыныс, генерация және аномалия табу."},
                {"title": "3) Тар және күшті ЖИ", "text": "Тар ЖИ нақты бір міндетте күшті. Күшті ЖИ — зерттеу мақсаты; өндірісте көбіне тар шешімдер қолданылады."},
                {"title": "4) Шектеулер", "text": "Дерек өзгерсе не белгілеу сапасы төмен болса, модель қателеседі. Мониторинг пен адам бақылауы қажет."},
                {"title": "5) Енгізу циклі", "text": "Мақсат → дерек → baseline → эксперимент → валидация → пилот → production мониторинг."},
            ],
            "practice": "Күнделікті қолданатын бір сервисті алып, ЖИ қолдануға болатын 3 орынды сипаттаңыз: кіріс, шығыс, метрика.",
            "glossary": [
                {"term": "Датасет", "definition": "Модельді оқыту және тексеруге арналған деректер жиыны."},
                {"term": "Инференс", "definition": "Үйретілген модельді жаңа дерекке қолдану."},
                {"term": "Метрика", "definition": "Модель сапасын өлшейтін сандық көрсеткіш."},
            ],
            "steps": [
                "Алдымен бизнес мақсаты мен өлшенетін нәтижені анықтаңыз.",
                "Деректің сапасы мен теңгерімін тексеріңіз.",
                "Алдымен baseline модель қолданып салыстырыңыз.",
                "Көрмеген деректерде сапаны тексеріңіз.",
                "Енгізуден кейін drift мониторингін жүргізіңіз.",
            ],
            "quiz": [
                {"id": "q1", "question": "ЖИ жобасының алғашқы қадамы қандай?", "options": ["Ең күрделі модель таңдау", "Мақсат пен метриканы анықтау", "Сервер санын көбейту"], "answer": 1},
                {"id": "q2", "question": "Инференс деген не?", "options": ["Дерек белгілеу", "Үйретілген модельді жаңа дерекке қолдану", "Шуды жою"], "answer": 1},
                {"id": "q3", "question": "Baseline не үшін керек?", "options": ["Бастапқы салыстыру шегін беру", "Барлық қателікті жою", "Интернетті тездету"], "answer": 0},
                {"id": "q4", "question": "Іске қосқаннан кейінгі негізгі қауіп?", "options": ["Түстер өзгеруі", "Data drift", "Модель атауы"], "answer": 1},
            ],
        },
        "ml-basics": {
            "overview": "Бұл сабақ ML циклін толық қамтиды: дерек дайындау, модель таңдау, бағалау және артық үйренуді азайту.",
            "sections": [
                {"title": "1) Деректер pipeline", "text": "Жинау, тазалау, кодтау, масштабтау және train/validation/test бөлу."},
                {"title": "2) Алгоритм таңдау", "text": "Сызықтық модель түсіндірмелі, бустинг кестелік деректе күшті, нейрондық желі күрделі белгілерге тиімді."},
                {"title": "3) Бағалау", "text": "Тек accuracy жеткіліксіз. Precision, recall, F1 және қате талдауы маңызды."},
            ],
            "practice": "Клиент кетуін болжау үшін: мақсат айнымалы, 5 белгі, 2 метрика, класс теңгерімсіздігіне 1 шешім ұсыныңыз.",
            "glossary": [
                {"term": "Train/Test split", "definition": "Оқыту мен тәуелсіз тексеруге деректі бөлу."},
                {"term": "Overfitting", "definition": "Модель жаттығу дерегін жаттап, жаңа деректе нашар жұмыс істеуі."},
                {"term": "Feature Engineering", "definition": "Ақпаратты белгілерді құрастыру процесі."},
            ],
            "steps": [
                "Жетпейтін мәндер мен дубльдерді тазалаңыз.",
                "Leakage болдырмай data split жасаңыз.",
                "Baseline оқытып метрикаларды тіркеңіз.",
                "Гиперпараметрлерді validation арқылы баптаңыз.",
                "Жаңа батчтарда тұрақтылықты тексеріңіз.",
            ],
            "quiz": [
                {"id": "q1", "question": "Test set не үшін керек?", "options": ["Гиперпараметр таңдау үшін", "Тәуелсіз финал бағалау үшін", "Лог сақтау үшін"], "answer": 1},
                {"id": "q2", "question": "Data leakage деген не?", "options": ["Жад аздығы", "Болашақ ақпаратты оқытуда қолдану", "Интернет баяу"], "answer": 1},
                {"id": "q3", "question": "Теңгерімсіз класта қай метрика пайдалы?", "options": ["Тек accuracy", "F1-score", "Тек жылдамдық"], "answer": 1},
                {"id": "q4", "question": "Артық үйренуді не азайтады?", "options": ["Бақылаусыз көп эпоха", "Регуляризация және validation", "Test set алып тастау"], "answer": 1},
            ],
        },
        "neural-basics": {
            "overview": "Бұл сабақ нейрондық желінің қалай үйренетінін: forward pass, loss және backpropagation арқылы түсіндіреді.",
            "sections": [
                {"title": "1) Архитектура", "text": "Қабаттар кіріс векторын пайдалы белгілер кеңістігіне түрлендіреді."},
                {"title": "2) Оқыту циклі", "text": "Forward pass болжам жасайды, loss қатені өлшейді, backpropagation градиент береді, optimizer салмақты жаңартады."},
                {"title": "3) Тұрақтылық", "text": "Нормализация, dropout, дұрыс learning rate және инициализация convergence жақсартады."},
            ],
            "practice": "Қолжазба цифрларын тануға арналған желіні сипаттаңыз: кіріс, 2 жасырын қабат, шығыс, loss және метрика.",
            "glossary": [
                {"term": "Activation Function", "definition": "ReLU, GELU, sigmoid сияқты сызықтық емес функция."},
                {"term": "Loss Function", "definition": "Болжам қатесін өлшейтін функция."},
                {"term": "Gradient", "definition": "Қатені азайту бағытын көрсететін шама."},
            ],
            "steps": [
                "Белгілерді нормализациялап tensor дайындаңыз.",
                "Forward pass арқылы болжам алыңыз.",
                "Loss есептеп қатені бағалаңыз.",
                "Backpropagation арқылы градиент есептеңіз.",
                "Adam/SGD арқылы салмақты жаңартыңыз.",
            ],
            "quiz": [
                {"id": "q1", "question": "Activation функция не үшін керек?", "options": ["Сызықтық емес тәуелділік беру", "Тек график үшін", "CSV сақтау үшін"], "answer": 0},
                {"id": "q2", "question": "Optimizer нені азайтады?", "options": ["Дерек көлемін", "Loss функциясын", "Қабат санын"], "answer": 1},
                {"id": "q3", "question": "Dropout не істейді?", "options": ["Оқытуда нейрондарды кездейсоқ өшіреді", "Белгіні өшіреді", "Интернетті тездетеді"], "answer": 0},
                {"id": "q4", "question": "Ненімен оқу тұрақсыз болуы мүмкін?", "options": ["Тым үлкен learning rate", "Нормализация", "Validation"], "answer": 0},
            ],
        },
    }

    extra_lessons: Dict[str, List[Dict[str, object]]] = {
        "ru": [
            {
                "id": "data-foundations",
                "title": "Данные для ИИ",
                "description": "Как качество и структура данных влияют на результат модели.",
                "overview": "Урок о том, почему данные важнее сложного алгоритма: сбор, разметка, очистка, баланс и контроль смещений.",
                "sections": [
                    {"title": "1) Источники данных", "text": "Логи, анкеты, датчики, CRM и внешние источники. Важно оценить полноту и юридическую допустимость использования.", "image": "images/sections/data-quality.jpg"},
                    {"title": "2) Подготовка", "text": "Очистка выбросов, обработка пропусков, унификация форматов и разметка классов."},
                    {"title": "3) Разметка и качество меток", "text": "Ошибки разметчиков напрямую ограничивают потолок качества модели. Используйте инструкции, двойную проверку и золотой набор."},
                    {"title": "4) Баланс и репрезентативность", "text": "Проверяйте перекос классов, дубликаты и шум. Выборка должна отражать реальное использование продукта."},
                    {"title": "5) Версионирование данных", "text": "Фиксируйте версии датасетов и пайплайнов, чтобы воспроизводить эксперименты и откатывать регрессии."},
                ],
                "practice": "Составьте чек-лист из 7 пунктов качества данных для проекта ИИ в вашей сфере.",
                "glossary": [
                    {"term": "Labeling", "definition": "Процесс присвоения правильных меток данным."},
                    {"term": "Bias", "definition": "Систематическое смещение данных, искажающее прогнозы."},
                    {"term": "Drift", "definition": "Изменение распределения данных со временем."},
                ],
                "steps": [
                    "Определите источники и формат хранения данных.",
                    "Проведите первичный аудит качества и полноты.",
                    "Сделайте очистку и нормализацию признаков.",
                    "Проверьте баланс классов и репрезентативность.",
                    "Подготовьте train/validation/test без утечек.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Что критичнее для качества ИИ-системы?", "options": ["Красивая презентация", "Качественные данные", "Длина названия модели"], "answer": 1},
                    {"id": "q2", "question": "Что такое drift?", "options": ["Случайный UI-эффект", "Сдвиг распределения данных со временем", "Тип базы данных"], "answer": 1},
                    {"id": "q3", "question": "Зачем нужен validation set?", "options": ["Для настройки гиперпараметров", "Для удаления логов", "Для стилизации интерфейса"], "answer": 0},
                    {"id": "q4", "question": "Что такое leakage?", "options": ["Утечка будущей информации в обучении", "Проблема CSS", "Падение FPS"], "answer": 0},
                ],
            },
            {
                "id": "ethics-safety",
                "title": "Этика и безопасность ИИ",
                "description": "Как делать ИИ-системы ответственными и безопасными для пользователей.",
                "overview": "Урок о практической этике: справедливость, прозрачность, приватность и безопасные ограничения на поведение моделей.",
                "sections": [
                    {"title": "1) Справедливость", "text": "Проверяйте метрики по разным группам пользователей, чтобы уменьшить дискриминацию и скрытые смещения в данных.", "image": "images/sections/ethics-team.jpg"},
                    {"title": "2) Прозрачность", "text": "Пользователь должен понимать, когда общается с ИИ, какие данные собираются и как принимается решение."},
                    {"title": "3) Приватность", "text": "Минимизируйте персональные данные, применяйте анонимизацию, шифрование и контроль доступа."},
                    {"title": "4) Безопасность", "text": "Вводите политики ответа, фильтры контента и процедуру ручной эскалации сложных случаев."},
                    {"title": "5) Ответственность", "text": "Назначьте владельца продукта и процесс расследования инцидентов: кто исправляет, кто информирует пользователей."},
                ],
                "practice": "Для чат-бота поддержки составьте 5 правил безопасного ответа, 3 сценария эскалации к человеку и чек-лист проверки fairness по двум группам пользователей.",
                "glossary": [
                    {"term": "Fairness", "definition": "Справедливость модели по отношению к разным группам."},
                    {"term": "PII", "definition": "Персонально идентифицируемая информация."},
                    {"term": "Guardrails", "definition": "Ограничения и правила безопасного поведения ИИ."},
                ],
                "steps": [
                    "Определите рискованные сценарии использования.",
                    "Сформулируйте политику безопасных ответов.",
                    "Добавьте фильтрацию контента и логирование.",
                    "Проводите регулярный аудит качества и рисков.",
                    "Подготовьте план инцидент-реагирования.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Что относится к приватности?", "options": ["Минимизация персональных данных", "Увеличение размера кнопок", "Изменение шрифтов"], "answer": 0},
                    {"id": "q2", "question": "Что такое guardrails?", "options": ["Графики обучения", "Ограничения безопасного поведения модели", "Тип нейрона"], "answer": 1},
                    {"id": "q3", "question": "Зачем делать аудит по группам пользователей?", "options": ["Для оценки fairness", "Только для дизайна", "Для ускорения CPU"], "answer": 0},
                    {"id": "q4", "question": "Что делать при опасном кейсе?", "options": ["Игнорировать", "Эскалировать человеку по процедуре", "Скрыть ответ"], "answer": 1},
                    {"id": "q5", "question": "Зачем проверять прозрачность?", "options": ["Чтобы пользователь понимал роль ИИ", "Чтобы ускорить GPU", "Чтобы скрыть ошибки"], "answer": 0},
                ],
            },
            {
                "id": "gen-ai-llm",
                "title": "Генеративный ИИ и LLM",
                "description": "Как работают большие языковые модели, промпты и ограничения.",
                "overview": "Урок о генеративном ИИ: токены, контекст, промпт-инжиниринг, RAG, галлюцинации и безопасное применение LLM в продуктах.",
                "sections": [
                    {"title": "1) Что такое LLM", "text": "Большая языковая модель предсказывает следующий токен по контексту. Обучается на огромных корпусах текстов, затем дообучается под задачи."},
                    {"title": "2) Промпты и контекст", "text": "Качество ответа зависит от инструкции, примеров (few-shot) и объёма контекстного окна. Структурируйте запрос: роль, задача, формат, ограничения."},
                    {"title": "3) RAG и знания", "text": "Retrieval-Augmented Generation подмешивает актуальные документы в промпт, снижая выдумки и устаревшие ответы."},
                    {"title": "4) Галлюцинации", "text": "Модель может уверенно выдавать неверные факты. Нужны проверка источников, цитирование и отказ отвечать при низкой уверенности."},
                    {"title": "5) Безопасное внедрение", "text": "Фильтры, лимиты, логирование, тестовые наборы промптов и человеческий review для чувствительных сценариев."},
                ],
                "practice": "Напишите промпт для ассистента поддержки: роль, 3 правила тона, формат ответа JSON и пример «безопасного отказа» при медицинском вопросе.",
                "glossary": [
                    {"term": "Токен", "definition": "Минимальная единица текста для модели (часть слова или символ)."},
                    {"term": "Prompt", "definition": "Инструкция и контекст, которые подаются модели перед генерацией."},
                    {"term": "RAG", "definition": "Подход: сначала поиск по базе знаний, затем генерация ответа с опорой на найденное."},
                    {"term": "Hallucination", "definition": "Правдоподобный, но фактически неверный ответ модели."},
                    {"term": "Fine-tuning", "definition": "Дообучение модели на узком домене или стиле ответов."},
                ],
                "steps": [
                    "Сформулируйте задачу и критерии качества ответа.",
                    "Соберите базу знаний или документы для RAG.",
                    "Напишите и протестируйте системный промпт на 10 кейсах.",
                    "Добавьте guardrails и сценарии отказа.",
                    "Измеряйте качество: точность, токсичность, задержку.",
                    "Внедрите мониторинг промптов и обратную связь пользователей.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Что делает LLM на каждом шаге?", "options": ["Предсказывает следующий токен", "Сканирует жёсткий диск", "Рисует интерфейс"], "answer": 0},
                    {"id": "q2", "question": "Зачем нужен RAG?", "options": ["Подмешать актуальные документы в контекст", "Увеличить размер кнопок", "Отключить сеть"], "answer": 0},
                    {"id": "q3", "question": "Что такое галлюцинация?", "options": ["Уверенный, но неверный ответ", "Сбой видеокарты", "Тип активации"], "answer": 0},
                    {"id": "q4", "question": "Что улучшает промпт?", "options": ["Чёткая роль, формат и ограничения", "Случайный набор эмодзи", "Пустой запрос"], "answer": 0},
                    {"id": "q5", "question": "Как снизить риск в продакшене?", "options": ["Guardrails и эскалация к человеку", "Полное отключение логов", "Один промпт на все домены"], "answer": 0},
                ],
            },
            {
                "id": "computer-vision",
                "title": "Компьютерное зрение",
                "description": "Как машины «видят» изображения: от пикселей до детекции объектов.",
                "overview": "Урок о том, как ИИ обрабатывает изображения: классификация, детекция, сегментация и типичные ошибки в продакшене.",
                "sections": [
                    {"title": "1) От пикселей к признакам", "text": "Сверточные сети (CNN) извлекают контуры, текстуры и формы. На ранних слоях — простые паттерны, на глубоких — объекты.", "image": "images/computer-vision.jpg"},
                    {"title": "2) Задачи CV", "text": "Классификация (что на фото), детекция (где объект), сегментация (пиксельная маска), трекинг в видео."},
                    {"title": "3) Данные и аугментация", "text": "Поворот, обрезка, шум и изменение освещения помогают модели не переобучаться на один ракурс."},
                    {"title": "4) Метрики", "text": "Accuracy, IoU для детекции, mAP. Важно смотреть ошибки на редких классах."},
                    {"title": "5) Продакшен", "text": "Учитывайте задержку, размер модели на edge-устройствах и смену условий съёмки (ночь, блики)."},
                ],
                "practice": "Опишите систему «умная камера на складе»: вход (разрешение, FPS), задача (детекция коробок), метрика и 2 риска.",
                "glossary": [
                    {"term": "CNN", "definition": "Сверточная нейросеть для изображений."},
                    {"term": "IoU", "definition": "Пересечение предсказанной и эталонной маски."},
                    {"term": "Augmentation", "definition": "Искусственное расширение обучающих изображений."},
                ],
                "steps": ["Соберите размеченный датасет.", "Обучите baseline-классификатор.", "Добавьте аугментацию.", "Оцените на hold-out.", "Проверьте на сложных кейсах (тень, размытие)."],
                "quiz": [
                    {"id": "q1", "question": "Что делает CNN?", "options": ["Извлекает признаки из изображения", "Только сжимает JPEG", "Хранит пароли"], "answer": 0},
                    {"id": "q2", "question": "Детекция vs классификация?", "options": ["Детекция находит объект и его место", "Это одно и то же", "Классификация только для видео"], "answer": 0},
                    {"id": "q3", "question": "Зачем аугментация?", "options": ["Улучшить обобщение модели", "Удалить метки", "Ускорить интернет"], "answer": 0},
                    {"id": "q4", "question": "IoU измеряет?", "options": ["Совпадение масок/боксов", "Скорость CPU", "Длину промпта"], "answer": 0},
                    {"id": "q5", "question": "Риск в продакшене CV?", "options": ["Смена освещения и ракурса", "Цвет кнопки", "Длина email"], "answer": 0},
                ],
            },
            {
                "id": "nlp-basics",
                "title": "Обработка естественного языка",
                "description": "Токены, эмбеддинги, классификация текста и поиск по смыслу.",
                "overview": "Урок о NLP: как текст превращается в числа, какие задачи решают модели и как оценивать качество на русском и других языках.",
                "sections": [
                    {"title": "1) Токенизация", "text": "Текст делится на токены (слова, подслова). От этого зависят словарь модели и стоимость запроса.", "image": "images/nlp-basics.jpg"},
                    {"title": "2) Эмбеддинги", "text": "Слова и предложения представляют векторами: близкие по смыслу — ближе в пространстве."},
                    {"title": "3) Задачи NLP", "text": "Классификация, извлечение сущностей (NER), суммаризация, перевод, поиск, вопрос-ответ."},
                    {"title": "4) Трансформеры", "text": "Архитектура внимания (attention) лежит в основе BERT, GPT и современных LLM."},
                    {"title": "5) Оценка", "text": "BLEU для перевода, F1 для NER, ручная оценка для чат-ботов и RAG-систем."},
                ],
                "practice": "Спроектируйте классификатор отзывов: 3 класса, 5 признаков текста, метрика F1 и пример плохого отзыва для теста.",
                "glossary": [
                    {"term": "Token", "definition": "Единица текста для модели."},
                    {"term": "Embedding", "definition": "Числовое представление слова или фразы."},
                    {"term": "NER", "definition": "Распознавание имён, дат, организаций в тексте."},
                ],
                "steps": ["Очистите и нормализуйте текст.", "Выберите токенизатор.", "Обучите или возьмите готовую модель.", "Оцените на тесте.", "Проверьте омонимы и сленг."],
                "quiz": [
                    {"id": "q1", "question": "Эмбеддинг — это?", "options": ["Векторное представление текста", "Тип базы данных", "CSS-стиль"], "answer": 0},
                    {"id": "q2", "question": "NER находит?", "options": ["Именованные сущности", "Только эмодзи", "Размер файла"], "answer": 0},
                    {"id": "q3", "question": "Attention в трансформере?", "options": ["Связывает слова по контексту", "Удаляет GPU", "Шифрует диск"], "answer": 0},
                    {"id": "q4", "question": "F1 полезен когда?", "options": ["Важен баланс precision и recall", "Нужен только дизайн", "Нет разметки"], "answer": 0},
                    {"id": "q5", "question": "Токенизация влияет на?", "options": ["Стоимость и длину контекста LLM", "Цвет navbar", "Версию Python"], "answer": 0},
                ],
            },
            {
                "id": "ai-product",
                "title": "ИИ в продукте",
                "description": "Как встроить модель в UX: метрики, A/B-тесты и работа с пользователями.",
                "overview": "Урок для тех, кто внедряет ИИ в реальный продукт: гипотезы, MVP, метрики бизнеса и итерации с обратной связью.",
                "sections": [
                    {"title": "1) От модели к фиче", "text": "Пользователю важен результат, а не F1-score. Определите сценарий: что человек делает до и после ИИ.", "image": "images/ai-product.jpg"},
                    {"title": "2) MVP и гипотезы", "text": "Начните с узкого кейса, измеримой гипотезы и быстрого пилота на реальных пользователях."},
                    {"title": "3) Метрики продукта", "text": "Сочетайте ML-метрики (точность) и продуктовые (конверсия, удержание, время до ответа)."},
                    {"title": "4) A/B-тесты", "text": "Сравнивайте варианты на одинаковой аудитории; следите за статистической значимостью."},
                    {"title": "5) Обратная связь", "text": "Кнопки «полезно/нет», разбор ошибок, дообучение и обновление промптов по логам."},
                ],
                "practice": "Опишите фичу «умные рекомендации» в приложении: гипотеза, 2 продуктовые метрики, риск и план отката.",
                "glossary": [
                    {"term": "MVP", "definition": "Минимальная версия продукта для проверки гипотезы."},
                    {"term": "A/B test", "definition": "Сравнение двух вариантов на пользователях."},
                    {"term": "North Star Metric", "definition": "Главная метрика ценности продукта."},
                ],
                "steps": ["Сформулируйте гипотезу.", "Определите north star и guardrail-метрики.", "Запустите пилот.", "Соберите фидбек.", "Итерируйте модель и UX."],
                "quiz": [
                    {"id": "q1", "question": "MVP в ИИ-продукте?", "options": ["Быстрая проверка ценности на узком кейсе", "Сразу максимальная модель", "Только презентация"], "answer": 0},
                    {"id": "q2", "question": "Guardrail-метрика?", "options": ["Ограничение вреда (латентность, токсичность)", "Цвет логотипа", "Число слайдов"], "answer": 0},
                    {"id": "q3", "question": "Зачем A/B?", "options": ["Сравнить варианты на данных", "Удалить пользователей", "Скрыть ошибки"], "answer": 0},
                    {"id": "q4", "question": "Что важнее для UX?", "options": ["Понятный результат для пользователя", "Только размер модели", "Случайный ответ"], "answer": 0},
                    {"id": "q5", "question": "Фидбек пользователей нужен для?", "options": ["Улучшения модели и сценариев", "Смены шрифта", "Отключения БД"], "answer": 0},
                ],
            },
            {
                "id": "ai-career",
                "title": "Карьера в ИИ",
                "description": "Роли, навыки и путь входа в профессию: от новичка до специалиста.",
                "overview": "Урок о карьерных траекториях в ИИ: какие роли существуют, какие навыки нужны на каждом этапе, как собрать портфолио и подготовиться к собеседованию.",
                "sections": [
                    {"title": "1) Роли в экосистеме ИИ", "text": "Data Scientist, ML Engineer, MLOps, AI Product Manager, Research Scientist, Prompt Engineer. Роли пересекаются, но фокус разный: исследование, код, инфраструктура или продукт.", "image": "images/ai-career.jpg"},
                    {"title": "2) Базовые навыки", "text": "Python, основы ML, статистика, работа с данными, Git. Для инженерных ролей — Linux, Docker, API. Для продуктовых — метрики, UX, коммуникация с бизнесом."},
                    {"title": "3) Портфолио", "text": "2–3 проекта с описанием задачи, данных, метрик и выводов лучше десятка туториалов без контекста. Публикуйте на GitHub с README и воспроизводимым кодом."},
                    {"title": "4) Обучение и сертификации", "text": "Курсы дают структуру, но работодатели смотрят на проекты. Сертификаты — плюс, но не замена практике. Участвуйте в Kaggle, хакатонах и open source."},
                    {"title": "5) Собеседование", "text": "Готовьтесь к задачам на ML, SQL, Python, system design для ML-систем и кейсам «как бы вы построили фичу». Объясняйте ход мысли, а не только финальный ответ."},
                ],
                "practice": "Составьте личный план на 6 месяцев: целевая роль, 3 навыка для прокачки, 1 проект для портфолио и 2 источника для нетворкинга.",
                "glossary": [
                    {"term": "ML Engineer", "definition": "Инженер, который внедряет и поддерживает ML-модели в продакшене."},
                    {"term": "Portfolio", "definition": "Набор проектов, демонстрирующих ваши навыки работодателю."},
                    {"term": "Kaggle", "definition": "Платформа с соревнованиями по ML и открытыми датасетами."},
                ],
                "steps": [
                    "Выберите целевую роль и изучите типичные требования в вакансиях.",
                    "Оцените текущий уровень по Python, ML и статистике.",
                    "Запланируйте один проект с измеримым результатом.",
                    "Оформите README: задача, данные, метрики, выводы.",
                    "Подготовьте 5-minute pitch о себе и своих проектах.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Что важнее для работодателя?", "options": ["Только сертификаты", "Реальные проекты с метриками", "Количество подписок в соцсетях"], "answer": 1},
                    {"id": "q2", "question": "ML Engineer в основном занимается?", "options": ["Только презентациями", "Внедрением и поддержкой моделей", "Только разметкой данных"], "answer": 1},
                    {"id": "q3", "question": "Зачем участвовать в Kaggle?", "options": ["Практика на реальных задачах", "Замена Git", "Отключение тестов"], "answer": 0},
                    {"id": "q4", "question": "Что включить в README проекта?", "options": ["Задачу, данные, метрики и выводы", "Только скриншот", "Список фильмов"], "answer": 0},
                    {"id": "q5", "question": "На собеседовании важно?", "options": ["Объяснять ход рассуждений", "Молчать до ответа", "Избегать вопросов"], "answer": 0},
                ],
            },
            {
                "id": "ai-agents",
                "title": "ИИ-агенты и автоматизация",
                "description": "Как агенты планируют, вызывают инструменты и выполняют многошаговые задачи.",
                "overview": "Урок об ИИ-агентах: архитектура plan-act-observe, tool calling, память, оркестрация и безопасное применение в бизнес-процессах.",
                "sections": [
                    {"title": "1) Что такое агент", "text": "Агент — LLM плюс цикл: получить цель → спланировать шаги → вызвать инструменты (API, БД, код) → проверить результат → повторить или завершить.", "image": "images/ai-agents.svg"},
                    {"title": "2) Tool calling", "text": "Модель не выполняет действия сама — она выбирает функцию и аргументы. Сервер выполняет вызов и возвращает результат в контекст для следующего шага."},
                    {"title": "3) Память и контекст", "text": "Краткосрочная память — история диалога. Долгосрочная — векторная база, профиль пользователя, логи прошлых сессий. Без памяти агент «забывает» цели."},
                    {"title": "4) Оркестрация", "text": "Один агент или несколько специализированных (researcher, coder, reviewer). Фреймворки помогают задавать граф шагов и лимиты."},
                    {"title": "5) Риски и guardrails", "text": "Агент может зациклиться, вызвать опасный API или «галлюцинировать» успех. Нужны лимиты итераций, whitelist инструментов, подтверждение критичных действий человеком."},
                ],
                "practice": "Спроектируйте агента для обработки заявок в поддержку: 3 инструмента, лимит 5 шагов, правило эскалации к человеку и метрика успеха.",
                "glossary": [
                    {"term": "Tool calling", "definition": "Вызов внешних функций или API по решению модели."},
                    {"term": "ReAct", "definition": "Паттерн Reason + Act: рассуждение и действие в одном цикле."},
                    {"term": "Orchestration", "definition": "Координация нескольких агентов или шагов в workflow."},
                ],
                "steps": [
                    "Сформулируйте цель агента и границы ответственности.",
                    "Определите список разрешённых инструментов.",
                    "Напишите системный промпт с правилами и форматом шагов.",
                    "Задайте лимит итераций и таймауты.",
                    "Протестируйте на 10 сценариях, включая сбойные.",
                    "Добавьте логирование каждого tool call.",
                ],
                "quiz": [
                    {"id": "q1", "question": "ИИ-агент отличается от чата тем, что?", "options": ["Может планировать и вызывать инструменты", "Только генерирует текст", "Не использует LLM"], "answer": 0},
                    {"id": "q2", "question": "Tool calling — это?", "options": ["Выбор функции и аргументов моделью", "Случайный клик по UI", "Тип базы данных"], "answer": 0},
                    {"id": "q3", "question": "Зачем лимит итераций?", "options": ["Предотвратить бесконечный цикл", "Ускорить CSS", "Скрыть логи"], "answer": 0},
                    {"id": "q4", "question": "Долгосрочная память агента?", "options": ["Векторная база или профиль", "Только цвет кнопки", "Версия Python"], "answer": 0},
                    {"id": "q5", "question": "Критичное действие в агенте?", "options": ["Подтверждение человеком", "Автозапуск без проверки", "Отключение логов"], "answer": 0},
                ],
            },
            {
                "id": "mlops-basics",
                "title": "MLOps: от эксперимента до продакшена",
                "description": "Версионирование, деплой, мониторинг и воспроизводимость ML-систем.",
                "overview": "Урок о MLOps: как довести модель от ноутбука до стабильного сервиса с CI/CD, мониторингом дрейфа и откатом версий.",
                "sections": [
                    {"title": "1) Воспроизводимость", "text": "Фиксируйте версии данных, кода, зависимостей и гиперпараметров. MLflow, DVC и контейнеры помогают повторить эксперимент через месяц.", "image": "images/sections/pipeline.jpg"},
                    {"title": "2) Обучение и артефакты", "text": "Сохраняйте веса модели, препроцессинг, метрики и конфиг. Pipeline: train → evaluate → register → deploy только при прохождении порогов."},
                    {"title": "3) Деплой", "text": "REST API, batch-скоринг, edge. Учитывайте latency, масштабирование и cold start. Canary и blue-green снижают риск при выкатке."},
                    {"title": "4) Мониторинг", "text": "Следите за latency, ошибками API, распределением признаков и качеством на отложенных метках. Алерты при drift и падении метрик."},
                    {"title": "5) Откат и governance", "text": "Храните N последних версий модели. Документируйте владельца, SLA и процедуру отката при инциденте."},
                ],
                "practice": "Опишите pipeline для модели оттока: 4 этапа, 3 метрики мониторинга, порог для алерта и план отката на предыдущую версию.",
                "glossary": [
                    {"term": "MLOps", "definition": "Практики DevOps, адаптированные для жизненного цикла ML."},
                    {"term": "Model registry", "definition": "Хранилище версий моделей с метаданными и статусами."},
                    {"term": "Canary deployment", "definition": "Выкатка новой версии на малую долю трафика для проверки."},
                ],
                "steps": [
                    "Версионируйте код и данные в репозитории.",
                    "Автоматизируйте train и evaluate в CI.",
                    "Регистрируйте модель только при прохождении порогов.",
                    "Деплойте через API с health-check.",
                    "Настройте мониторинг drift и latency.",
                    "Документируйте процедуру отката.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Зачем версионировать данные?", "options": ["Воспроизвести эксперимент", "Ускорить CSS", "Скрыть метрики"], "answer": 0},
                    {"id": "q2", "question": "Model registry хранит?", "options": ["Версии моделей и метаданные", "Только пароли", "Скриншоты UI"], "answer": 0},
                    {"id": "q3", "question": "Canary deployment — это?", "options": ["Проверка на части трафика", "Удаление модели", "Полный отказ от тестов"], "answer": 0},
                    {"id": "q4", "question": "Что мониторить в продакшене?", "options": ["Drift, latency, ошибки", "Только цвет логотипа", "Длину email"], "answer": 0},
                    {"id": "q5", "question": "При инциденте сначала?", "options": ["Откат на стабильную версию", "Удалить все логи", "Переобучить без данных"], "answer": 0},
                ],
            },
            {
                "id": "reinforcement-learning",
                "title": "Обучение с подкреплением",
                "description": "Агент, среда, награда и политика: как ИИ учится действиями.",
                "overview": "Урок о reinforcement learning: MDP, Q-learning, policy gradient, exploration vs exploitation и примеры: игры, робототехника, рекомендации.",
                "sections": [
                    {"title": "1) Агент и среда", "text": "Агент наблюдает состояние, выбирает действие, получает награду. Среда переходит в новое состояние. Цель — максимизировать суммарную награду.", "image": "images/reinforcement-learning.svg"},
                    {"title": "2) Награда и политика", "text": "Награда задаёт желаемое поведение. Политика π(a|s) — правило выбора действий. Плохая награда приводит к нежелательным стратегиям."},
                    {"title": "3) Exploration vs exploitation", "text": "Баланс между пробой новых действий и использованием лучшего известного. ε-greedy, UCB — классические приёмы."},
                    {"title": "4) Q-learning и DQN", "text": "Q(s,a) — ожидаемая награда. Табличный Q-learning для малых пространств; DQN — нейросеть для больших состояний (Atari, роботы)."},
                    {"title": "5) Применение", "text": "Игры, управление ресурсами, персонализация, робототехника. В продакшене важны симуляторы и безопасные sandbox-среды."},
                ],
                "practice": "Опишите RL-задачу для рекомендации контента: состояние, действие, награда и риск «залипания» пользователя в одном типе контента.",
                "glossary": [
                    {"term": "MDP", "definition": "Markov Decision Process — формальная модель среды с состояниями и наградами."},
                    {"term": "Policy", "definition": "Стратегия выбора действий агентом."},
                    {"term": "Reward shaping", "definition": "Проектирование функции награды для ускорения обучения."},
                ],
                "steps": [
                    "Определите состояние, действия и награду.",
                    "Проверьте, что награда отражает бизнес-цель.",
                    "Начните с простого baseline (случайная или эвристика).",
                    "Обучите агента в симуляторе.",
                    "Оцените exploration и стабильность политики.",
                ],
                "quiz": [
                    {"id": "q1", "question": "RL отличается от supervised тем, что?", "options": ["Учится по награде, без готовых меток на каждом шаге", "Только на размеченных данных", "Не использует агента"], "answer": 0},
                    {"id": "q2", "question": "Политика — это?", "options": ["Правило выбора действий", "Тип базы данных", "Функция активации"], "answer": 0},
                    {"id": "q3", "question": "Exploration нужен для?", "options": ["Найти лучшие действия", "Удалить среду", "Скрыть награду"], "answer": 0},
                    {"id": "q4", "question": "Q(s,a) оценивает?", "options": ["Ожидаемую награду действия в состоянии", "Размер датасета", "Скорость API"], "answer": 0},
                    {"id": "q5", "question": "Плохая награда приводит к?", "options": ["Нежелательному поведению агента", "Мгновенному идеалу", "Отключению среды"], "answer": 0},
                ],
            },
            {
                "id": "statistics-for-ai",
                "title": "Статистика для ИИ",
                "description": "Вероятность, распределения, выборки и A/B — база для ML и экспериментов.",
                "overview": "Урок о статистических основах ИИ: как интерпретировать данные, оценивать неопределённость и принимать решения по результатам экспериментов.",
                "sections": [
                    {"title": "1) Описательная статистика", "text": "Среднее, медиана, дисперсия, квартили. Выбросы и асимметрия влияют на модели — смотрите распределения, а не только среднее.", "image": "images/statistics-for-ai.svg"},
                    {"title": "2) Вероятность", "text": "События, условная вероятность, независимость. Байесовский подход обновляет убеждения при появлении новых данных."},
                    {"title": "3) Выборки и оценки", "text": "Выборка должна быть репрезентативной. Доверительные интервалы показывают неопределённость оценки. Большая выборка — уже интервал."},
                    {"title": "4) Гипотезы и p-value", "text": "Нулевая гипотеза, уровень значимости α, ошибки I и II рода. p-value — не «вероятность истины», а мера противоречия данным при H0."},
                    {"title": "5) A/B и causality", "text": "Случайное разбиение, достаточный размер выборки, одна метрика-решение. Корреляция ≠ причинность; контролируйте confounders."},
                ],
                "practice": "Спроектируйте A/B-тест новой рекомендации: гипотеза, метрика, минимальный размер выборки (качественно), длительность и критерий остановки.",
                "glossary": [
                    {"term": "Confidence interval", "definition": "Диапазон, в котором с заданной вероятностью лежит истинный параметр."},
                    {"term": "p-value", "definition": "Вероятность получить такие или более экстремальные данные при верной H0."},
                    {"term": "Standard deviation", "definition": "Мера разброса значений относительно среднего."},
                ],
                "steps": [
                    "Постройте гистограмму и опишите распределение.",
                    "Проверьте выбросы и пропуски.",
                    "Сформулируйте нулевую и альтернативную гипотезы.",
                    "Выберите уровень α и метрику.",
                    "Интерпретируйте результат с доверительным интервалом.",
                ],
                "quiz": [
                    {"id": "q1", "question": "Медиана устойчива к?", "options": ["Выбросам", "Только к среднему", "Отсутствию данных"], "answer": 0},
                    {"id": "q2", "question": "p-value малый означает?", "options": ["Данные редки при H0", "H0 точно ложна", "Модель идеальна"], "answer": 0},
                    {"id": "q3", "question": "A/B-тест требует?", "options": ["Случайного разбиения пользователей", "Одного пользователя", "Только визуала"], "answer": 0},
                    {"id": "q4", "question": "Корреляция означает причинность?", "options": ["Не всегда", "Всегда", "Никогда не связаны"], "answer": 0},
                    {"id": "q5", "question": "Доверительный интервал показывает?", "options": ["Неопределённость оценки", "Точный ответ навсегда", "Цвет графика"], "answer": 0},
                ],
            },
        ],
        "en": [
            {
                "id": "data-foundations",
                "title": "Data Foundations for AI",
                "description": "How data quality and structure shape model performance.",
                "overview": "This lesson explains why data quality often matters more than model complexity.",
                "sections": [
                    {"title": "1) Data sources", "text": "Logs, forms, sensors, CRM, and third-party datasets with legal and quality checks."},
                    {"title": "2) Preparation", "text": "Cleaning outliers, handling missing values, standardizing formats, and labeling."},
                    {"title": "3) Quality control", "text": "Track class imbalance, duplicates, and noisy labels before training."},
                ],
                "practice": "Create a 7-point data quality checklist for your domain.",
                "glossary": [
                    {"term": "Labeling", "definition": "Assigning correct target labels to samples."},
                    {"term": "Bias", "definition": "Systematic skew in data that distorts predictions."},
                    {"term": "Drift", "definition": "Distribution changes in data over time."},
                ],
                "steps": ["Define data sources and ownership.", "Audit quality and completeness.", "Clean and normalize features.", "Check representativeness.", "Build leakage-free train/val/test splits."],
                "quiz": [
                    {"id": "q1", "question": "What impacts AI quality most?", "options": ["Presentation slides", "High-quality data", "Long model names"], "answer": 1},
                    {"id": "q2", "question": "What is data drift?", "options": ["UI animation", "Data distribution change over time", "Database type"], "answer": 1},
                    {"id": "q3", "question": "Why use validation data?", "options": ["Hyperparameter tuning", "Delete logs", "Style UI"], "answer": 0},
                    {"id": "q4", "question": "What is leakage?", "options": ["Future information in training", "CSS issue", "FPS drop"], "answer": 0},
                ],
            },
            {
                "id": "ethics-safety",
                "title": "AI Ethics and Safety",
                "description": "Build responsible and safe AI features for real users.",
                "overview": "A practical lesson on fairness, privacy, transparency, and guardrails.",
                "sections": [
                    {"title": "1) Fairness", "text": "Evaluate outcomes across user groups to reduce discriminatory behavior."},
                    {"title": "2) Privacy", "text": "Minimize PII, anonymize sensitive data, and enforce access control."},
                    {"title": "3) Safety", "text": "Use response policies, content filters, and human escalation workflows."},
                ],
                "practice": "Draft 5 safety rules and 3 human-escalation scenarios for a support chatbot.",
                "glossary": [
                    {"term": "Fairness", "definition": "Equitable model behavior across different groups."},
                    {"term": "PII", "definition": "Personally identifiable information."},
                    {"term": "Guardrails", "definition": "Policies and constraints that keep model behavior safe."},
                ],
                "steps": ["Identify high-risk scenarios.", "Define safe-response policy.", "Add filtering and logging.", "Audit behavior regularly.", "Prepare incident response process."],
                "quiz": [
                    {"id": "q1", "question": "What supports privacy?", "options": ["PII minimization", "Bigger buttons", "Changing fonts"], "answer": 0},
                    {"id": "q2", "question": "What are guardrails?", "options": ["Training charts", "Safety behavior constraints", "Neuron type"], "answer": 1},
                    {"id": "q3", "question": "Why evaluate by user groups?", "options": ["To measure fairness", "Only for design", "To speed CPU"], "answer": 0},
                    {"id": "q4", "question": "What to do in risky cases?", "options": ["Ignore it", "Escalate to human workflow", "Hide output"], "answer": 1},
                    {"id": "q5", "question": "Why improve transparency?", "options": ["Users understand AI's role", "Faster GPU only", "Hide all errors"], "answer": 0},
                ],
            },
            {
                "id": "gen-ai-llm",
                "title": "Generative AI and LLMs",
                "description": "How large language models work, prompting, and limits.",
                "overview": "Generative AI lesson: tokens, context windows, prompt design, RAG, hallucinations, and safe LLM deployment.",
                "sections": [
                    {"title": "1) What is an LLM", "text": "A large language model predicts the next token from context, trained on massive text corpora and optionally fine-tuned."},
                    {"title": "2) Prompts and context", "text": "Answer quality depends on instructions, few-shot examples, and context length. Structure prompts: role, task, format, constraints."},
                    {"title": "3) RAG", "text": "Retrieval-Augmented Generation injects fresh documents into the prompt to reduce stale or fabricated answers."},
                    {"title": "4) Hallucinations", "text": "Models may sound confident but be wrong. Use citations, source checks, and refusal policies."},
                    {"title": "5) Safe deployment", "text": "Filters, rate limits, logging, prompt test suites, and human review for sensitive flows."},
                ],
                "practice": "Write a support-assistant prompt: role, 3 tone rules, JSON output format, and a safe refusal example for medical questions.",
                "glossary": [
                    {"term": "Token", "definition": "Smallest text unit processed by the model."},
                    {"term": "Prompt", "definition": "Instruction and context sent before generation."},
                    {"term": "RAG", "definition": "Retrieve documents first, then generate grounded answers."},
                    {"term": "Hallucination", "definition": "Plausible but incorrect model output."},
                    {"term": "Fine-tuning", "definition": "Additional training on a specific domain or style."},
                ],
                "steps": ["Define task and answer quality criteria.", "Prepare a knowledge base for RAG.", "Draft and test a system prompt on 10 cases.", "Add guardrails and refusal paths.", "Measure accuracy, toxicity, and latency.", "Monitor prompts and user feedback."],
                "quiz": [
                    {"id": "q1", "question": "What does an LLM predict?", "options": ["Next token", "Disk sectors", "CSS colors"], "answer": 0},
                    {"id": "q2", "question": "Why use RAG?", "options": ["Inject fresh documents", "Resize buttons", "Disable network"], "answer": 0},
                    {"id": "q3", "question": "What is a hallucination?", "options": ["Confident but wrong answer", "GPU driver bug", "Activation type"], "answer": 0},
                    {"id": "q4", "question": "What improves prompts?", "options": ["Clear role, format, constraints", "Random emojis only", "Empty input"], "answer": 0},
                    {"id": "q5", "question": "How to reduce production risk?", "options": ["Guardrails and human escalation", "Disable all logs", "One prompt for every domain"], "answer": 0},
                ],
            },
            {
                "id": "computer-vision",
                "title": "Computer Vision",
                "description": "How machines see images: from pixels to object detection.",
                "overview": "Image classification, detection, segmentation, augmentation, and production pitfalls.",
                "sections": [
                    {"title": "1) Pixels to features", "text": "CNNs extract edges, textures, and objects layer by layer.", "image": "images/computer-vision.jpg"},
                    {"title": "2) CV tasks", "text": "Classification, detection, segmentation, and video tracking."},
                    {"title": "3) Data & augmentation", "text": "Rotations, crops, and lighting changes improve generalization."},
                    {"title": "4) Metrics", "text": "Accuracy, IoU, mAP — especially on rare classes."},
                    {"title": "5) Production", "text": "Latency, edge deployment, and changing capture conditions."},
                ],
                "practice": "Design a warehouse smart-camera system: input, task, metric, and two risks.",
                "glossary": [{"term": "CNN", "definition": "Convolutional network for images."}, {"term": "IoU", "definition": "Overlap of prediction and ground truth."}, {"term": "Augmentation", "definition": "Synthetic training image variations."}],
                "steps": ["Collect labeled data.", "Train a baseline.", "Add augmentation.", "Evaluate on hold-out.", "Test hard cases."],
                "quiz": [
                    {"id": "q1", "question": "CNNs are used to?", "options": ["Extract image features", "Compress JPEG only", "Store passwords"], "answer": 0},
                    {"id": "q2", "question": "Detection differs from classification how?", "options": ["Finds object and location", "They are identical", "Only for video"], "answer": 0},
                    {"id": "q3", "question": "Augmentation helps?", "options": ["Generalization", "Delete labels", "Speed up Wi-Fi"], "answer": 0},
                    {"id": "q4", "question": "IoU measures?", "options": ["Mask/box overlap", "CPU speed", "Prompt length"], "answer": 0},
                    {"id": "q5", "question": "CV production risk?", "options": ["Lighting and angle shift", "Button color", "Email length"], "answer": 0},
                ],
            },
            {
                "id": "nlp-basics",
                "title": "Natural Language Processing",
                "description": "Tokens, embeddings, text classification, and semantic search.",
                "overview": "How text becomes numbers, core NLP tasks, transformers, and evaluation.",
                "sections": [
                    {"title": "1) Tokenization", "text": "Text splits into tokens; this drives vocabulary size and LLM cost.", "image": "images/nlp-basics.jpg"},
                    {"title": "2) Embeddings", "text": "Similar meaning maps to nearby vectors."},
                    {"title": "3) NLP tasks", "text": "Classification, NER, summarization, translation, QA, search."},
                    {"title": "4) Transformers", "text": "Attention powers BERT, GPT, and modern LLMs."},
                    {"title": "5) Evaluation", "text": "BLEU, F1 for NER, human review for chatbots and RAG."},
                ],
                "practice": "Design a review classifier: 3 classes, 5 text features, F1 metric, and one hard test example.",
                "glossary": [{"term": "Token", "definition": "Text unit for the model."}, {"term": "Embedding", "definition": "Numeric text representation."}, {"term": "NER", "definition": "Named entity recognition."}],
                "steps": ["Clean text.", "Pick tokenizer.", "Train or use a pretrained model.", "Evaluate on test.", "Check slang and ambiguity."],
                "quiz": [
                    {"id": "q1", "question": "Embedding is?", "options": ["Vector text representation", "Database type", "CSS style"], "answer": 0},
                    {"id": "q2", "question": "NER finds?", "options": ["Named entities", "Only emojis", "File size"], "answer": 0},
                    {"id": "q3", "question": "Attention in transformers?", "options": ["Links words by context", "Removes GPU", "Encrypts disk"], "answer": 0},
                    {"id": "q4", "question": "F1 is useful when?", "options": ["Precision-recall balance matters", "Design only", "No labels"], "answer": 0},
                    {"id": "q5", "question": "Tokenization affects?", "options": ["LLM cost and context length", "Navbar color", "Python version"], "answer": 0},
                ],
            },
            {
                "id": "ai-product",
                "title": "AI in Product",
                "description": "Shipping models in UX: metrics, A/B tests, and user feedback.",
                "overview": "Hypotheses, MVP, business metrics, and iteration loops for real AI features.",
                "sections": [
                    {"title": "1) Model to feature", "text": "Users care about outcomes, not F1 alone.", "image": "images/ai-product.jpg"},
                    {"title": "2) MVP", "text": "Start narrow with a measurable hypothesis and real users."},
                    {"title": "3) Product metrics", "text": "Combine ML metrics with conversion, retention, and latency."},
                    {"title": "4) A/B tests", "text": "Compare variants on the same audience with significance checks."},
                    {"title": "5) Feedback loops", "text": "Thumbs up/down, error review, prompt and model updates."},
                ],
                "practice": "Describe a smart recommendations feature: hypothesis, 2 product metrics, risk, rollback plan.",
                "glossary": [{"term": "MVP", "definition": "Minimum product to test a hypothesis."}, {"term": "A/B test", "definition": "Compare two variants on users."}, {"term": "North Star", "definition": "Primary value metric."}],
                "steps": ["Write hypothesis.", "Define north star and guardrails.", "Run pilot.", "Collect feedback.", "Iterate model and UX."],
                "quiz": [
                    {"id": "q1", "question": "AI MVP means?", "options": ["Fast value test on narrow case", "Largest model first", "Slides only"], "answer": 0},
                    {"id": "q2", "question": "Guardrail metric?", "options": ["Limits harm (latency, toxicity)", "Logo color", "Slide count"], "answer": 0},
                    {"id": "q3", "question": "Why A/B?", "options": ["Compare variants with data", "Delete users", "Hide errors"], "answer": 0},
                    {"id": "q4", "question": "UX priority?", "options": ["Clear user outcome", "Model size only", "Random answers"], "answer": 0},
                    {"id": "q5", "question": "User feedback helps?", "options": ["Improve models and flows", "Change fonts", "Disable DB"], "answer": 0},
                ],
            },
            {
                "id": "ai-career",
                "title": "Career in AI",
                "description": "Roles, skills, and a path from beginner to specialist.",
                "overview": "Career paths in AI: roles, skills per stage, portfolio building, and interview preparation.",
                "sections": [
                    {"title": "1) AI roles", "text": "Data Scientist, ML Engineer, MLOps, AI PM, Research Scientist, Prompt Engineer — different focus on research, code, infra, or product.", "image": "images/ai-career.jpg"},
                    {"title": "2) Core skills", "text": "Python, ML basics, statistics, data work, Git. Engineers add Linux, Docker, APIs. Product roles need metrics and UX."},
                    {"title": "3) Portfolio", "text": "2–3 projects with problem, data, metrics, and conclusions beat many tutorial clones. Publish on GitHub with a clear README."},
                    {"title": "4) Learning", "text": "Courses give structure; employers look at projects. Certificates help but do not replace practice. Try Kaggle and open source."},
                    {"title": "5) Interviews", "text": "Prepare ML tasks, SQL, Python, ML system design, and product cases. Explain your reasoning, not only final answers."},
                ],
                "practice": "Draft a 6-month plan: target role, 3 skills to improve, one portfolio project, and two networking sources.",
                "glossary": [
                    {"term": "ML Engineer", "definition": "Builds and maintains ML models in production."},
                    {"term": "Portfolio", "definition": "Projects that demonstrate your skills to employers."},
                    {"term": "Kaggle", "definition": "Platform for ML competitions and datasets."},
                ],
                "steps": ["Pick a target role.", "Assess Python, ML, and stats.", "Plan one measurable project.", "Write a strong README.", "Prepare a 5-minute self pitch."],
                "quiz": [
                    {"id": "q1", "question": "What do employers value most?", "options": ["Certificates only", "Real projects with metrics", "Social followers only"], "answer": 1},
                    {"id": "q2", "question": "ML Engineers mainly?", "options": ["Only slides", "Deploy and maintain models", "Only label data"], "answer": 1},
                    {"id": "q3", "question": "Why join Kaggle?", "options": ["Practice on real tasks", "Replace Git", "Skip tests"], "answer": 0},
                    {"id": "q4", "question": "README should include?", "options": ["Problem, data, metrics, conclusions", "Only a screenshot", "Movie list"], "answer": 0},
                    {"id": "q5", "question": "In interviews, show?", "options": ["Your reasoning process", "Silence until the end", "Avoid questions"], "answer": 0},
                ],
            },
            {
                "id": "ai-agents",
                "title": "AI Agents and Automation",
                "description": "How agents plan, call tools, and run multi-step workflows.",
                "overview": "AI agents: plan-act-observe loops, tool calling, memory, orchestration, and safe deployment.",
                "sections": [
                    {"title": "1) What is an agent", "text": "LLM plus a loop: goal → plan → tools (API, DB, code) → verify → repeat or finish.", "image": "images/ai-agents.svg"},
                    {"title": "2) Tool calling", "text": "The model picks a function and arguments; the server executes and returns results to context."},
                    {"title": "3) Memory", "text": "Short-term: chat history. Long-term: vector store, user profile, session logs."},
                    {"title": "4) Orchestration", "text": "Single agent or specialized team (researcher, coder, reviewer) with step graphs and limits."},
                    {"title": "5) Safety", "text": "Use iteration caps, tool whitelists, and human approval for critical actions."},
                ],
                "practice": "Design a support-ticket agent: 3 tools, 5-step limit, human escalation rule, success metric.",
                "glossary": [
                    {"term": "Tool calling", "definition": "Model-driven invocation of external functions or APIs."},
                    {"term": "ReAct", "definition": "Reason and act in one iterative loop."},
                    {"term": "Orchestration", "definition": "Coordinating multiple agents or workflow steps."},
                ],
                "steps": ["Define agent goal.", "List allowed tools.", "Write system prompt.", "Set iteration limits.", "Test 10 scenarios.", "Log every tool call."],
                "quiz": [
                    {"id": "q1", "question": "Agents differ from chat how?", "options": ["Plan and use tools", "Text only", "No LLM"], "answer": 0},
                    {"id": "q2", "question": "Tool calling is?", "options": ["Model picks function + args", "Random UI click", "DB type"], "answer": 0},
                    {"id": "q3", "question": "Iteration limits prevent?", "options": ["Infinite loops", "Faster CSS", "Hidden logs"], "answer": 0},
                    {"id": "q4", "question": "Long-term memory?", "options": ["Vector store or profile", "Button color", "Python version"], "answer": 0},
                    {"id": "q5", "question": "Critical actions need?", "options": ["Human approval", "Auto-run always", "No logs"], "answer": 0},
                ],
            },
            {
                "id": "mlops-basics",
                "title": "MLOps Basics",
                "description": "Versioning, deployment, monitoring, and reproducible ML systems.",
                "overview": "From notebook to production: CI/CD, drift monitoring, and model rollback.",
                "sections": [
                    {"title": "1) Reproducibility", "text": "Pin data, code, dependencies, and hyperparameters. Use MLflow, DVC, or containers.", "image": "images/sections/pipeline.jpg"},
                    {"title": "2) Artifacts", "text": "Save weights, preprocessing, metrics, config. Train → evaluate → register → deploy on thresholds."},
                    {"title": "3) Deployment", "text": "REST API, batch scoring, edge. Watch latency, scale, cold start. Canary reduces rollout risk."},
                    {"title": "4) Monitoring", "text": "Track latency, errors, feature distributions, and delayed labels. Alert on drift."},
                    {"title": "5) Rollback", "text": "Keep recent model versions and document owners, SLA, and incident rollback."},
                ],
                "practice": "Outline a churn model pipeline: 4 stages, 3 monitor metrics, alert threshold, rollback plan.",
                "glossary": [
                    {"term": "MLOps", "definition": "DevOps practices for the ML lifecycle."},
                    {"term": "Model registry", "definition": "Versioned store of models and metadata."},
                    {"term": "Canary deployment", "definition": "Roll out to a small traffic slice first."},
                ],
                "steps": ["Version code and data.", "Automate train/eval in CI.", "Register on pass.", "Deploy with health checks.", "Monitor drift.", "Document rollback."],
                "quiz": [
                    {"id": "q1", "question": "Why version data?", "options": ["Reproduce experiments", "Speed CSS", "Hide metrics"], "answer": 0},
                    {"id": "q2", "question": "Model registry holds?", "options": ["Model versions + metadata", "Passwords only", "UI screenshots"], "answer": 0},
                    {"id": "q3", "question": "Canary means?", "options": ["Test on partial traffic", "Delete model", "Skip all tests"], "answer": 0},
                    {"id": "q4", "question": "Monitor in prod?", "options": ["Drift, latency, errors", "Logo color", "Email length"], "answer": 0},
                    {"id": "q5", "question": "On incident first?", "options": ["Rollback stable version", "Delete logs", "Retrain without data"], "answer": 0},
                ],
            },
            {
                "id": "reinforcement-learning",
                "title": "Reinforcement Learning",
                "description": "Agent, environment, reward, and policy — learning by action.",
                "overview": "RL basics: MDP, Q-learning, exploration vs exploitation, games and robotics.",
                "sections": [
                    {"title": "1) Agent and environment", "text": "Observe state, act, get reward, new state. Maximize total reward.", "image": "images/reinforcement-learning.svg"},
                    {"title": "2) Reward and policy", "text": "Reward shapes behavior. Policy π(a|s) picks actions. Bad rewards → bad strategies."},
                    {"title": "3) Explore vs exploit", "text": "Balance trying new actions vs using the best known. ε-greedy is a classic trick."},
                    {"title": "4) Q-learning and DQN", "text": "Q(s,a) estimates expected return. DQN uses neural nets for large state spaces."},
                    {"title": "5) Applications", "text": "Games, resource control, personalization, robotics. Simulators help safe training."},
                ],
                "practice": "Define an RL content recommender: state, action, reward, and filter-bubble risk.",
                "glossary": [
                    {"term": "MDP", "definition": "Markov Decision Process formalizing states and rewards."},
                    {"term": "Policy", "definition": "Strategy for choosing actions."},
                    {"term": "Reward shaping", "definition": "Designing rewards to speed learning."},
                ],
                "steps": ["Define state, actions, reward.", "Align reward with business goal.", "Start with a baseline.", "Train in a simulator.", "Check policy stability."],
                "quiz": [
                    {"id": "q1", "question": "RL vs supervised?", "options": ["Learns from reward signals", "Only labeled rows", "No agent"], "answer": 0},
                    {"id": "q2", "question": "Policy is?", "options": ["Action selection rule", "Database type", "Activation fn"], "answer": 0},
                    {"id": "q3", "question": "Exploration helps?", "options": ["Find better actions", "Delete environment", "Hide reward"], "answer": 0},
                    {"id": "q4", "question": "Q(s,a) estimates?", "options": ["Expected return of action in state", "Dataset size", "API speed"], "answer": 0},
                    {"id": "q5", "question": "Bad reward causes?", "options": ["Undesired agent behavior", "Instant perfection", "No environment"], "answer": 0},
                ],
            },
            {
                "id": "statistics-for-ai",
                "title": "Statistics for AI",
                "description": "Probability, distributions, sampling, and A/B tests for ML.",
                "overview": "Statistical foundations: describe data, quantify uncertainty, and run sound experiments.",
                "sections": [
                    {"title": "1) Descriptive stats", "text": "Mean, median, variance, quartiles. Outliers and skew matter — inspect distributions.", "image": "images/statistics-for-ai.svg"},
                    {"title": "2) Probability", "text": "Events, conditional probability, independence. Bayes updates beliefs with new data."},
                    {"title": "3) Sampling", "text": "Representative samples and confidence intervals show estimate uncertainty."},
                    {"title": "4) Hypothesis tests", "text": "H0, significance α, type I/II errors. p-value measures conflict with H0, not truth probability."},
                    {"title": "5) A/B and causality", "text": "Random assignment, adequate sample size. Correlation is not causation."},
                ],
                "practice": "Design an A/B test for a new recommender: hypothesis, metric, sample size (qualitative), duration, stop rule.",
                "glossary": [
                    {"term": "Confidence interval", "definition": "Range likely containing the true parameter."},
                    {"term": "p-value", "definition": "Probability of data this extreme if H0 is true."},
                    {"term": "Standard deviation", "definition": "Spread around the mean."},
                ],
                "steps": ["Plot distribution.", "Check outliers.", "State H0 and H1.", "Pick α and metric.", "Interpret with CI."],
                "quiz": [
                    {"id": "q1", "question": "Median is robust to?", "options": ["Outliers", "Only the mean", "Missing all data"], "answer": 0},
                    {"id": "q2", "question": "Small p-value means?", "options": ["Rare data if H0 true", "H0 surely false", "Perfect model"], "answer": 0},
                    {"id": "q3", "question": "A/B needs?", "options": ["Random user split", "One user only", "Visuals only"], "answer": 0},
                    {"id": "q4", "question": "Correlation implies causation?", "options": ["Not always", "Always", "Never related"], "answer": 0},
                    {"id": "q5", "question": "Confidence interval shows?", "options": ["Estimate uncertainty", "Exact forever answer", "Chart color"], "answer": 0},
                ],
            },
        ],
        "kk": [
            {
                "id": "data-foundations",
                "title": "ЖИ үшін дерек негіздері",
                "description": "Дерек сапасы мен құрылымы модель нәтижесіне қалай әсер етеді.",
                "overview": "Бұл сабақ дерек сапасы неге күрделі модельден де маңызды болуы мүмкін екенін түсіндіреді.",
                "sections": [
                    {"title": "1) Дерек көздері", "text": "Логтар, формалар, сенсорлар, CRM және сыртқы дереккөздер."},
                    {"title": "2) Дайындау", "text": "Шуды тазалау, бос мәндерді өңдеу, форматты біріздендіру және белгілеу."},
                    {"title": "3) Сапаны бақылау", "text": "Класс теңгерімі, дубликат және қате белгілерді тексеру қажет."},
                ],
                "practice": "Өз салаңыз үшін дерек сапасына арналған 7 тармақтан тұратын чек-лист құрыңыз.",
                "glossary": [
                    {"term": "Labeling", "definition": "Дерекке дұрыс нысана меткасын беру."},
                    {"term": "Bias", "definition": "Болжамды бұрмалайтын жүйелі қисықтық."},
                    {"term": "Drift", "definition": "Уақыт өте дерек таралуының өзгеруі."},
                ],
                "steps": ["Дерек көздерін анықтаңыз.", "Сапа аудитін жасаңыз.", "Белгілерді тазалап нормалаңыз.", "Репрезентативтілікті тексеріңіз.", "Leakage жоқ split құрыңыз."],
                "quiz": [
                    {"id": "q1", "question": "ЖИ сапасына не көбірек әсер етеді?", "options": ["Слайд дизайны", "Сапалы дерек", "Ұзын атау"], "answer": 1},
                    {"id": "q2", "question": "Data drift деген не?", "options": ["UI эффект", "Уақыт өте дерек таралуының өзгеруі", "БД түрі"], "answer": 1},
                    {"id": "q3", "question": "Validation не үшін керек?", "options": ["Гиперпараметр баптау", "Лог жою", "UI бояу"], "answer": 0},
                    {"id": "q4", "question": "Leakage деген не?", "options": ["Болашақ ақпаратты оқытуда пайдалану", "CSS ақауы", "FPS түсуі"], "answer": 0},
                ],
            },
            {
                "id": "ethics-safety",
                "title": "ЖИ этикасы және қауіпсіздік",
                "description": "Пайдаланушыға қауіпсіз және жауапты ЖИ жасау қағидалары.",
                "overview": "Сабақ fairness, privacy, transparency және guardrails ұғымдарын практикалық тұрғыда береді.",
                "sections": [
                    {"title": "1) Әділеттілік", "text": "Әртүрлі топтар бойынша метрикаларды тексеріп, дискриминацияны азайтыңыз."},
                    {"title": "2) Құпиялылық", "text": "PII деректерін азайтып, анонимдеу және рұқсат бақылауын қолданыңыз."},
                    {"title": "3) Қауіпсіздік", "text": "Жауап саясаты, фильтрлер және адамға эскалация процесі қажет."},
                ],
                "practice": "Қолдау чат-боты үшін 5 қауіпсіздік ережесі және 3 эскалация сценарийін жазыңыз.",
                "glossary": [
                    {"term": "Fairness", "definition": "Модельдің әр топқа әділ жұмыс істеуі."},
                    {"term": "PII", "definition": "Жеке адамды анықтайтын дерек."},
                    {"term": "Guardrails", "definition": "Модельді қауіпсіз ұстайтын шектеулер."},
                ],
                "steps": ["Қауіпті сценарийлерді анықтаңыз.", "Қауіпсіз жауап саясатын құрыңыз.", "Фильтр мен логтауды қосыңыз.", "Тұрақты аудит жасаңыз.", "Инцидент жоспарын дайындаңыз."],
                "quiz": [
                    {"id": "q1", "question": "Құпиялылыққа не жатады?", "options": ["PII азайту", "Кнопканы үлкейту", "Қаріп ауыстыру"], "answer": 0},
                    {"id": "q2", "question": "Guardrails деген не?", "options": ["Оқу графигі", "Қауіпсіздік шектеулері", "Нейрон түрі"], "answer": 1},
                    {"id": "q3", "question": "Неге топтар бойынша бағалау керек?", "options": ["Fairness үшін", "Тек дизайн үшін", "CPU үдету үшін"], "answer": 0},
                    {"id": "q4", "question": "Қауіпті жағдайда не істеу керек?", "options": ["Елемеу", "Адамға эскалациялау", "Жауапты жасыру"], "answer": 1},
                    {"id": "q5", "question": "Ашықтық не үшін маңызды?", "options": ["Пайдаланушы ЖИ рөлін түсінеді", "Тек GPU жылдамдығы", "Қателерді жасыру"], "answer": 0},
                ],
            },
            {
                "id": "gen-ai-llm",
                "title": "Генеративті ЖИ және LLM",
                "description": "Үлкен тіл модельдері, промпт және шектеулер.",
                "overview": "Генеративті ЖИ сабағы: токен, контекст, промпт, RAG, галлюцинация және LLM-ді қауіпсіз енгізу.",
                "sections": [
                    {"title": "1) LLM деген не", "text": "Модель контекст бойынша келесі токенді болжайды. Үлкен мәтін корпустарында оқытылады, кейін тапсырмаға бейімделеді."},
                    {"title": "2) Промпт және контекст", "text": "Жауап сапасы нұсқау, few-shot мысалдар және контекст көлеміне байланысты."},
                    {"title": "3) RAG", "text": "Алдымен құжат іздеу, кейін сол негізде жауап генерациялау — ескірген ақпаратты азайтады."},
                    {"title": "4) Галлюцинация", "text": "Модель сенімді, бірақ қате факт беруі мүмкін. Дереккөз тексеруі мен бас тарту саясаты қажет."},
                    {"title": "5) Қауіпсіз енгізу", "text": "Фильтр, лимит, лог, промпт тесті және сезімтал сценарийлерде адам review."},
                ],
                "practice": "Қолдау боты үшін промпт жазыңыз: рөл, 3 тон ережесі, JSON формат және медициналық сұрақта қауіпсіз бас тарту мысалы.",
                "glossary": [
                    {"term": "Токен", "definition": "Модель өңдейтін мәтіннің ең кіші бірлігі."},
                    {"term": "Prompt", "definition": "Генерация алдында берілетін нұсқау мен контекст."},
                    {"term": "RAG", "definition": "Іздеу + генерация: жауап құжатқа сүйенеді."},
                    {"term": "Hallucination", "definition": "Сенімді көрінетін, бірақ қате жауап."},
                    {"term": "Fine-tuning", "definition": "Нақты доменде қосымша оқыту."},
                ],
                "steps": ["Міндет пен сапа критерийін анықтаңыз.", "RAG үшін білім базасын дайындаңыз.", "10 кейсте промпт тестілеңіз.", "Guardrails қосыңыз.", "Дәлдік пен кідірісті өлшеңіз.", "Промпт мониторингін жүргізіңіз."],
                "quiz": [
                    {"id": "q1", "question": "LLM не болжайды?", "options": ["Келесі токен", "Диск секторы", "CSS түсі"], "answer": 0},
                    {"id": "q2", "question": "RAG не үшін?", "options": ["Жаңа құжатты контекстке қосу", "Кнопканы үлкейту", "Желіні өшіру"], "answer": 0},
                    {"id": "q3", "question": "Галлюцинация деген не?", "options": ["Сенімді, бірақ қате жауап", "GPU ақауы", "Активация түрі"], "answer": 0},
                    {"id": "q4", "question": "Промптті не жақсартады?", "options": ["Анық рөл, формат, шектеу", "Кездейсоқ эмодзи", "Бос сұрау"], "answer": 0},
                    {"id": "q5", "question": "Production тәуекелін қалай азайту?", "options": ["Guardrails және адамға эскалация", "Барлық логты өшіру", "Бір промпт барлық доменге"], "answer": 0},
                ],
            },
            {
                "id": "computer-vision",
                "title": "Компьютерлік көру",
                "description": "Машина кескінді қалай «көреді»: пиксельден объектіге.",
                "overview": "Классификация, детекция, сегментация, аугментация және production тәуекелдері.",
                "sections": [
                    {"title": "1) Пиксельден белгіге", "text": "CNN контур, текстура және объектілерді шығарады.", "image": "images/computer-vision.jpg"},
                    {"title": "2) CV міндеттері", "text": "Классификация, детекция, сегментация, бейне трекинг."},
                    {"title": "3) Аугментация", "text": "Айналдыру, кесу, жарық өзгерісі — модельдің тұрақтылығы."},
                    {"title": "4) Метрикалар", "text": "Accuracy, IoU, mAP."},
                    {"title": "5) Production", "text": "Кідіріс, edge және түсірілім жағдайлары."},
                ],
                "practice": "Қойма камерасы жүйесін сипаттаңыз: кіріс, міндет, метрика, 2 тәуекел.",
                "glossary": [{"term": "CNN", "definition": "Кескінге арналған желілік."}, {"term": "IoU", "definition": "Болжам мен эталон қиылысы."}, {"term": "Augmentation", "definition": "Жасанды кескін кеңейту."}],
                "steps": ["Дерек жина.", "Baseline оқыту.", "Аугментация.", "Тест бағалау.", "Қиын кейстер."],
                "quiz": [
                    {"id": "q1", "question": "CNN не үшін?", "options": ["Кескін белгілерін шығару", "Тек JPEG", "Құпиясөз"], "answer": 0},
                    {"id": "q2", "question": "Детекция?", "options": ["Орын мен объект", "Бірдей", "Тек бейне"], "answer": 0},
                    {"id": "q3", "question": "Аугментация?", "options": ["Жалпылау", "Метка жою", "Wi-Fi"], "answer": 0},
                    {"id": "q4", "question": "IoU?", "options": ["Қиылыс", "CPU", "Промпт"], "answer": 0},
                    {"id": "q5", "question": "Production тәуекел?", "options": ["Жарық өзгерісі", "Түс", "Email"], "answer": 0},
                ],
            },
            {
                "id": "nlp-basics",
                "title": "Табиғи тілді өңдеу",
                "description": "Токен, эмбеддинг, мәтін классификациясы.",
                "overview": "Мәтінді сандарға айналдыру, NLP міндеттері, трансформер, бағалау.",
                "sections": [
                    {"title": "1) Токенизация", "text": "Мәтін токендерге бөлінеді.", "image": "images/nlp-basics.jpg"},
                    {"title": "2) Эмбеддинг", "text": "Мағына жақын векторлар жақын."},
                    {"title": "3) NLP міндеттері", "text": "Классификация, NER, қысқарту, аударма."},
                    {"title": "4) Трансформер", "text": "Attention — BERT, GPT негізі."},
                    {"title": "5) Бағалау", "text": "BLEU, F1, адам review."},
                ],
                "practice": "Пікір классификаторы: 3 класс, 5 белгі, F1.",
                "glossary": [{"term": "Token", "definition": "Мәтін бірлігі."}, {"term": "Embedding", "definition": "Векторлық көрініс."}, {"term": "NER", "definition": "Атау тану."}],
                "steps": ["Мәтін тазала.", "Токенизатор.", "Модель.", "Тест.", "Сленг тексер."],
                "quiz": [
                    {"id": "q1", "question": "Эмбеддинг?", "options": ["Вектор", "БД", "CSS"], "answer": 0},
                    {"id": "q2", "question": "NER?", "options": ["Атаулар", "Эмодзи", "Файл"], "answer": 0},
                    {"id": "q3", "question": "Attention?", "options": ["Контекст байланысы", "GPU жою", "Шифр"], "answer": 0},
                    {"id": "q4", "question": "F1?", "options": ["Precision-recall", "Дизайн", "Метка жоқ"], "answer": 0},
                    {"id": "q5", "question": "Токенизация?", "options": ["LLM құны", "Түс", "Python"], "answer": 0},
                ],
            },
            {
                "id": "ai-product",
                "title": "Өнімдегі ЖИ",
                "description": "Модельді UX-ке енгізу: метрика, A/B, фидбек.",
                "overview": "Гипотеза, MVP, бизнес метрикалары, итерация.",
                "sections": [
                    {"title": "1) Модель → фича", "text": "Пайдаланушыға нәтиже маңызды.", "image": "images/ai-product.jpg"},
                    {"title": "2) MVP", "text": "Тар кейс, өлшенетін гипотеза."},
                    {"title": "3) Метрикалар", "text": "ML + конверсия, retention."},
                    {"title": "4) A/B", "text": "Вариант салыстыру."},
                    {"title": "5) Фидбек", "text": "Лог, review, жаңарту."},
                ],
                "practice": "Ұсыныс фичасы: гипотеза, 2 метрика, тәуекел.",
                "glossary": [{"term": "MVP", "definition": "Минималды өнім."}, {"term": "A/B", "definition": "Салыстыру тесті."}, {"term": "North Star", "definition": "Негізгі метрика."}],
                "steps": ["Гипотеза.", "Метрика.", "Пилот.", "Фидбек.", "Итерация."],
                "quiz": [
                    {"id": "q1", "question": "MVP?", "options": ["Тез тексеру", "Ең үлкен модель", "Слайд"], "answer": 0},
                    {"id": "q2", "question": "Guardrail?", "options": ["Зиян шектеу", "Логотип", "Слайд"], "answer": 0},
                    {"id": "q3", "question": "A/B?", "options": ["Дерекпен салыстыру", "Жою", "Жасыру"], "answer": 0},
                    {"id": "q4", "question": "UX?", "options": ["Түсінікті нәтиже", "Тек модель", "Кездейсоқ"], "answer": 0},
                    {"id": "q5", "question": "Фидбек?", "options": ["Жақсарту", "Қаріп", "БД өшіру"], "answer": 0},
                ],
            },
            {
                "id": "ai-career",
                "title": "ЖИ-де мансап",
                "description": "Рөлдер, дағдылар және маманға дейінгі жол.",
                "overview": "ЖИ мансабы: рөлдер, дағдылар, портфолио және сұхбатқа дайындық.",
                "sections": [
                    {"title": "1) ЖИ рөлдері", "text": "Data Scientist, ML Engineer, MLOps, AI PM — зерттеу, код, инфра немесе өнім.", "image": "images/ai-career.jpg"},
                    {"title": "2) Негізгі дағдылар", "text": "Python, ML, статистика, дерек, Git. Инженерлерге Docker, API."},
                    {"title": "3) Портфолио", "text": "2–3 нақты жоба көп туториалдан жақсы. GitHub + README."},
                    {"title": "4) Оқу", "text": "Курстар құрылым береді; жобалар маңыздырақ. Kaggle, open source."},
                    {"title": "5) Сұхбат", "text": "ML, SQL, Python, system design дайындығы. Ойлау процесін түсіндіріңіз."},
                ],
                "practice": "6 айлық жоспар: мақсатты рөл, 3 дағды, 1 портфолио жобасы, 2 нетворкинг көзі.",
                "glossary": [
                    {"term": "ML Engineer", "definition": "Production-дағы модельді енгізетін маман."},
                    {"term": "Portfolio", "definition": "Дағдыларды көрсететін жобалар жиынтығы."},
                    {"term": "Kaggle", "definition": "ML жарыстары платформасы."},
                ],
                "steps": ["Рөл таңда.", "Дағды бағала.", "Жоба жоспарла.", "README жаз.", "Pitch дайында."],
                "quiz": [
                    {"id": "q1", "question": "Жұмыс беруші неге қарайды?", "options": ["Тек сертификат", "Нақты жобалар", "Жазылушылар"], "answer": 1},
                    {"id": "q2", "question": "ML Engineer?", "options": ["Тек слайд", "Модель енгізу", "Тек белгілеу"], "answer": 1},
                    {"id": "q3", "question": "Kaggle не үшін?", "options": ["Практика", "Git ауыстыру", "Тест өшіру"], "answer": 0},
                    {"id": "q4", "question": "README-де?", "options": ["Міндет, дерек, метрика", "Тек скрин", "Фильм"], "answer": 0},
                    {"id": "q5", "question": "Сұхбатта?", "options": ["Ойлауды түсіндіру", "Үнсіздік", "Сұрақтан қашу"], "answer": 0},
                ],
            },
            {
                "id": "ai-agents",
                "title": "ЖИ-агенттер",
                "description": "Жоспарлау, tool calling және көп қадамды workflow.",
                "overview": "Агент: мақсат → жоспар → құрал → тексеру. Қауіпсіздік және оркестрация.",
                "sections": [
                    {"title": "1) Агент", "text": "LLM + цикл: мақсат, құрал, нәтиже.", "image": "images/ai-agents.svg"},
                    {"title": "2) Tool calling", "text": "Модель функция таңдайды, сервер орындайды."},
                    {"title": "3) Жад", "text": "Қысқа: диалог. Ұзақ: вектор база, профиль."},
                    {"title": "4) Оркестрация", "text": "Бір немесе бірнеше маман агент, шектеулер."},
                    {"title": "5) Қауіпсіздік", "text": "Итерация лимиті, whitelist, адам растауы."},
                ],
                "practice": "Қолдау агенті: 3 құрал, 5 қадам, эскалация, метрика.",
                "glossary": [
                    {"term": "Tool calling", "definition": "API шақыру."},
                    {"term": "ReAct", "definition": "Ойлау + әрекет циклі."},
                    {"term": "Orchestration", "definition": "Workflow координациясы."},
                ],
                "steps": ["Мақсат.", "Құралдар.", "Промпт.", "Лимит.", "Тест.", "Лог."],
                "quiz": [
                    {"id": "q1", "question": "Агент чаттан?", "options": ["Құрал қолданады", "Тек мәтін", "LLM жоқ"], "answer": 0},
                    {"id": "q2", "question": "Tool calling?", "options": ["Функция таңдау", "UI клик", "БД түрі"], "answer": 0},
                    {"id": "q3", "question": "Лимит не үшін?", "options": ["Шексіз циклді болдырмау", "CSS", "Лог жою"], "answer": 0},
                    {"id": "q4", "question": "Ұзақ жад?", "options": ["Вектор база", "Түс", "Python"], "answer": 0},
                    {"id": "q5", "question": "Критик әрекет?", "options": ["Адам растауы", "Авто", "Лог өшіру"], "answer": 0},
                ],
            },
            {
                "id": "mlops-basics",
                "title": "MLOps негіздері",
                "description": "Нұсқа, deploy, мониторинг.",
                "overview": "Ноутбуктан production-ға: CI/CD, drift, rollback.",
                "sections": [
                    {"title": "1) Қайталау", "text": "Дерек, код, dependency нұсқалау.", "image": "images/sections/pipeline.jpg"},
                    {"title": "2) Артефакт", "text": "Салмақ, preprocessing, метрика сақтау."},
                    {"title": "3) Deploy", "text": "API, batch, edge. Canary."},
                    {"title": "4) Мониторинг", "text": "Latency, drift, қате."},
                    {"title": "5) Rollback", "text": "Ескі нұсқаға оралу жоспары."},
                ],
                "practice": "Churn pipeline: 4 кезең, 3 метрика, alert, rollback.",
                "glossary": [
                    {"term": "MLOps", "definition": "ML lifecycle инженериясы."},
                    {"term": "Model registry", "definition": "Модель нұсқалары."},
                    {"term": "Canary", "definition": "Кіші трафикке deploy."},
                ],
                "steps": ["Version.", "CI.", "Register.", "Deploy.", "Monitor.", "Rollback жоспар."],
                "quiz": [
                    {"id": "q1", "question": "Дерек version?", "options": ["Эксперимент қайталау", "CSS", "Метрика жасыру"], "answer": 0},
                    {"id": "q2", "question": "Registry?", "options": ["Модель нұсқалары", "Құпиясөз", "Скрин"], "answer": 0},
                    {"id": "q3", "question": "Canary?", "options": ["Бөлік трафик", "Жою", "Тест жоқ"], "answer": 0},
                    {"id": "q4", "question": "Мониторинг?", "options": ["Drift, latency", "Түс", "Email"], "answer": 0},
                    {"id": "q5", "question": "Инцидент?", "options": ["Rollback", "Лог жою", "Дерексіз оқыту"], "answer": 0},
                ],
            },
            {
                "id": "reinforcement-learning",
                "title": "Reinforcement Learning",
                "description": "Агент, орта, сыйақы, policy.",
                "overview": "RL: MDP, Q-learning, exploration, қолдану.",
                "sections": [
                    {"title": "1) Агент", "text": "Күй → әрекет → сыйақы.", "image": "images/reinforcement-learning.svg"},
                    {"title": "2) Сыйақы", "text": "Сыйақы мінез-құлықты анықтайды."},
                    {"title": "3) Exploration", "text": "Жаңа әрекет vs ең жақсы белгілі."},
                    {"title": "4) Q-learning", "text": "Q(s,a) күтілетін сыйақы."},
                    {"title": "5) Қолдану", "text": "Ойын, робот, ұсыныс."},
                ],
                "practice": "Контент ұсынысы RL: күй, әрекет, сыйақы, filter bubble тәуекелі.",
                "glossary": [
                    {"term": "MDP", "definition": "Markov Decision Process."},
                    {"term": "Policy", "definition": "Әрекет стратегиясы."},
                    {"term": "Reward shaping", "definition": "Сыйақы жобалау."},
                ],
                "steps": ["Күй, әрекет, сыйақы.", "Бизнес мақсат.", "Baseline.", "Симулятор.", "Тұрақтылық."],
                "quiz": [
                    {"id": "q1", "question": "RL supervised-тан?", "options": ["Сыйақымен оқиды", "Тек белгі", "Агент жоқ"], "answer": 0},
                    {"id": "q2", "question": "Policy?", "options": ["Әрекет ережесі", "БД", "Активация"], "answer": 0},
                    {"id": "q3", "question": "Exploration?", "options": ["Жақсы әрекет табу", "Ортаны жою", "Сыйақы жасыру"], "answer": 0},
                    {"id": "q4", "question": "Q(s,a)?", "options": ["Күтілетін сыйақы", "Дерек көлемі", "API"], "answer": 0},
                    {"id": "q5", "question": "Жаман сыйақы?", "options": ["Қалаусыз мінез", "Дәлдік", "Орта өшіру"], "answer": 0},
                ],
            },
            {
                "id": "statistics-for-ai",
                "title": "ЖИ үшін статистика",
                "description": "Ықтималдық, таралу, A/B тест.",
                "overview": "Статистика негізі: дерек сипаттау, белгісіздік, эксперимент.",
                "sections": [
                    {"title": "1) Сипаттау", "text": "Орта, медиана, дисперсия.", "image": "images/statistics-for-ai.svg"},
                    {"title": "2) Ықтималдық", "text": "Оқиға, шартты ықтималдық."},
                    {"title": "3) Выборка", "text": "Сенімділік интервалы."},
                    {"title": "4) Гипотеза", "text": "H0, p-value, α."},
                    {"title": "5) A/B", "text": "Кездейсоқ бөлу. Корреляция ≠ себеп."},
                ],
                "practice": "A/B тест: гипотеза, метрика, ұзақтығы, тоқтату ережесі.",
                "glossary": [
                    {"term": "Confidence interval", "definition": "Баға белгісіздігі."},
                    {"term": "p-value", "definition": "H0 кезіндегі дерек ықтималдығы."},
                    {"term": "Standard deviation", "definition": "Ортадан шашырау."},
                ],
                "steps": ["Гистограмма.", "Выброс.", "H0/H1.", "α.", "CI түсіндіру."],
                "quiz": [
                    {"id": "q1", "question": "Медиана?", "options": ["Выбросқа төзімді", "Тек орта", "Дерек жоқ"], "answer": 0},
                    {"id": "q2", "question": "Кіші p-value?", "options": ["H0-да сирек дерек", "H0 жалған", "Модель идеал"], "answer": 0},
                    {"id": "q3", "question": "A/B?", "options": ["Кездейсоқ бөлу", "Бір адам", "Тек визуал"], "answer": 0},
                    {"id": "q4", "question": "Корреляция?", "options": ["Себеп емес әрқашан", "Әрқашан себеп", "Ешқашан"], "answer": 0},
                    {"id": "q5", "question": "CI?", "options": ["Белгісіздік", "Дәл жауап", "Түс"], "answer": 0},
                ],
            },
        ],
    }

    lesson_images = {
        "intro-ai": "images/intro-ai.jpg",
        "ml-basics": "images/ml-basics.jpg",
        "neural-basics": "images/neural-basics.jpg",
        "data-foundations": "images/data-foundations.jpg",
        "ethics-safety": "images/ethics-safety.jpg",
        "gen-ai-llm": "images/gen-ai-llm.jpg",
        "computer-vision": "images/computer-vision.jpg",
        "nlp-basics": "images/nlp-basics.jpg",
        "ai-product": "images/ai-product.jpg",
        "ai-career": "images/ai-career.jpg",
        "ai-agents": "images/ai-agents.svg",
        "mlops-basics": "images/mlops-basics.svg",
        "reinforcement-learning": "images/reinforcement-learning.svg",
        "statistics-for-ai": "images/statistics-for-ai.svg",
    }
    lesson_image_fallbacks = {
        "intro-ai": "images/intro-ai.svg",
        "ml-basics": "images/ml-basics.svg",
        "neural-basics": "images/neural-basics.svg",
        "data-foundations": "images/data-foundations.svg",
        "ethics-safety": "images/ethics-safety.svg",
        "gen-ai-llm": "images/gen-ai-llm.svg",
        "computer-vision": "images/computer-vision.svg",
        "nlp-basics": "images/nlp-basics.svg",
        "ai-product": "images/ai-product.svg",
        "ai-career": "images/ai-career.svg",
        "ai-agents": "images/ai-agents.svg",
        "mlops-basics": "images/mlops-basics.svg",
        "reinforcement-learning": "images/reinforcement-learning.svg",
        "statistics-for-ai": "images/statistics-for-ai.svg",
    }

    for lang, entries in extra_lessons.items():
        lesson_catalog[lang].extend(entries)

    for lang, lessons in lesson_catalog.items():
        for lesson in lessons:
            extension = deep_lessons.get(lang, {}).get(lesson["id"])
            if extension:
                lesson.update(extension)
            lesson_id = lesson["id"]
            lesson["image"] = lesson_images.get(lesson_id, "images/intro-ai.jpg")
            lesson["image_fallback"] = lesson_image_fallbacks.get(
                lesson_id, "images/intro-ai.svg"
            )
            apply_lesson_meta(lesson)

    lesson_index = {
        lang: {lesson["id"]: lesson for lesson in lessons}
        for lang, lessons in lesson_catalog.items()
    }

    def get_lang() -> str:
        lang = request.args.get("lang") or session.get("lang", "ru")
        if lang not in translations:
            lang = "ru"
        session["lang"] = lang
        return lang

    def t(key: str, lang: str) -> str:
        return translations.get(lang, translations["ru"]).get(key, key)

    def login_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login", lang=get_lang()))
            return fn(*args, **kwargs)

        return wrapped

    with app.app_context():
        init_schema(app)

    @app.context_processor
    def inject_globals():
        lang = session.get("lang", "ru")
        return {
            "current_lang": lang,
            "t": lambda key: t(key, lang),
        }

    @app.route("/")
    def index():
        lang = get_lang()
        return render_template(
            "index.html",
            lang=lang,
            topics=lesson_catalog[lang],
            message=request.args.get("message", ""),
        )

    @app.route("/register", methods=["GET", "POST"])
    def register():
        lang = get_lang()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if name and email and password:
                db = get_db()
                try:
                    db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    db.commit()
                    return redirect(
                        url_for(
                            "login",
                            lang=lang,
                            message=t("message_register_success", lang),
                        )
                    )
                except INTEGRITY_ERRORS:
                    return render_template(
                        "register.html",
                        lang=lang,
                        message=t("message_user_exists", lang),
                    )
        return render_template("register.html", lang=lang, message="")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        lang = get_lang()
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("dashboard", lang=lang))
            return render_template(
                "login.html",
                lang=lang,
                message=t("message_login_error", lang),
            )
        return render_template(
            "login.html",
            lang=lang,
            message=request.args.get("message", ""),
        )

    @app.route("/logout")
    def logout():
        lang = get_lang()
        session.pop("user_id", None)
        session.pop("user_name", None)
        return redirect(url_for("index", lang=lang))

    def achievement_name(ach_id: str, lang: str) -> str:
        key = achievement_labels.get(lang, achievement_labels["ru"]).get(ach_id, ach_id)
        return t(key, lang)

    def build_lesson_rows(lang: str, user_id: int) -> tuple:
        db = get_db()
        lesson_ids = [lesson["id"] for lesson in lesson_catalog[lang]]
        rows = db.execute(
            """
            SELECT lesson_id, completed, quiz_score, total_questions
            FROM progress
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        progress_map = {row["lesson_id"]: row for row in rows}
        bookmarked = get_bookmarks(db, user_id)
        lessons = []
        for lesson in lesson_catalog[lang]:
            row = progress_map.get(lesson["id"])
            lessons.append(
                {
                    **lesson,
                    "completed": bool(row["completed"]) if row else False,
                    "quiz_score": int(row["quiz_score"]) if row else 0,
                    "total_questions": int(row["total_questions"]) if row else len(lesson["quiz"]),
                    "bookmarked": lesson["id"] in bookmarked,
                }
            )
        completed_count = sum(1 for lesson in lessons if lesson["completed"])
        total = len(lesson_ids)
        progress_percent = int((completed_count / total) * 100) if total else 0
        return lessons, progress_map, completed_count, progress_percent, bookmarked

    @app.route("/dashboard")
    @login_required
    def dashboard():
        lang = get_lang()
        user_id = session["user_id"]
        db = get_db()
        stats = touch_streak(db, user_id)
        xp = int(stats.get("xp") or 0)
        streak = int(stats.get("streak_days") or 0)
        lessons, progress_map, completed_count, progress_percent, bookmarked = build_lesson_rows(
            lang, user_id
        )
        achievements = compute_achievements(
            completed_count,
            len(lessons),
            xp,
            streak,
            progress_map,
            len(bookmarked),
        )
        for ach in achievements:
            ach["name"] = achievement_name(str(ach["id"]), lang)

        continue_id = next_lesson_id(lessons)
        continue_lesson = next(
            (lesson for lesson in lessons if lesson["id"] == continue_id), None
        )

        daily = None
        if lessons:
            pool = [lesson for lesson in lessons if lesson.get("quiz")]
            if pool:
                pick = random.choice(pool)
                question = random.choice(pick["quiz"])
                daily = {
                    "lesson_id": pick["id"],
                    "lesson_title": pick["title"],
                    "question": question["question"],
                    "options": question["options"],
                    "answer": question["answer"],
                }

        return render_template(
            "dashboard.html",
            lang=lang,
            user_name=session.get("user_name", ""),
            lessons=lessons,
            progress_percent=progress_percent,
            xp=xp,
            level=level_from_xp(xp),
            xp_next=xp_to_next_level(xp),
            streak=streak,
            achievements=achievements,
            continue_lesson=continue_lesson,
            daily_challenge=daily,
            notes_saved=request.args.get("notes_saved") == "1",
        )

    @app.route("/lesson/<lesson_id>")
    @login_required
    def lesson_detail(lesson_id: str):
        lang = get_lang()
        lesson = lesson_index[lang].get(lesson_id)
        if not lesson:
            return redirect(url_for("dashboard", lang=lang, message=t("not_found", lang)))

        db = get_db()
        saved = db.execute(
            """
            SELECT completed, quiz_score, total_questions
            FROM progress
            WHERE user_id = ? AND lesson_id = ?
            """,
            (session["user_id"], lesson_id),
        ).fetchone()
        score = int(saved["quiz_score"]) if saved else 0
        total = int(saved["total_questions"]) if saved else len(lesson["quiz"])
        user_id = session["user_id"]
        bookmarked = lesson_id in get_bookmarks(db, user_id)
        note = get_note(db, user_id, lesson_id)
        xp_gain = request.args.get("xp_gain", "")

        return render_template(
            "lesson.html",
            lang=lang,
            lesson=lesson,
            result_message=request.args.get("result_message", ""),
            score=score,
            total=total,
            completed=bool(saved["completed"]) if saved else False,
            bookmarked=bookmarked,
            note=note,
            xp_gain=xp_gain,
        )

    @app.route("/quiz/<lesson_id>", methods=["POST"])
    @login_required
    def submit_quiz(lesson_id: str):
        lang = get_lang()
        lesson = lesson_index[lang].get(lesson_id)
        if not lesson:
            return redirect(url_for("dashboard", lang=lang))

        correct = 0
        total_questions = len(lesson["quiz"])
        for question in lesson["quiz"]:
            selected = request.form.get(question["id"])
            if selected is not None and selected.isdigit() and int(selected) == question["answer"]:
                correct += 1

        passed = correct == total_questions
        feedback = t("quiz_feedback_good", lang) if passed else t("quiz_feedback_retry", lang)
        result_message = f"{t('quiz_result', lang)}: {correct}/{total_questions}. {feedback}"

        db = get_db()
        user_id = session["user_id"]
        was_done = db.execute(
            "SELECT completed FROM progress WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        ).fetchone()
        already_completed = bool(was_done and was_done["completed"])

        db.execute(
            """
            INSERT INTO progress (user_id, lesson_id, completed, quiz_score, total_questions)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                completed = excluded.completed,
                quiz_score = excluded.quiz_score,
                total_questions = excluded.total_questions,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, lesson_id, 1 if passed else 0, correct, total_questions),
        )
        db.commit()

        xp_gain = correct * 15
        if passed and not already_completed:
            xp_gain += int(lesson.get("xp_reward", 100))
        elif passed:
            xp_gain += 25
        touch_streak(db, user_id)
        add_xp(db, user_id, xp_gain)

        return redirect(
            url_for(
                "lesson_detail",
                lesson_id=lesson_id,
                lang=lang,
                result_message=result_message,
                xp_gain=xp_gain,
            )
        )

    @app.route("/complete/<lesson_id>", methods=["POST"])
    @login_required
    def complete_lesson(lesson_id: str):
        lang = get_lang()
        db = get_db()
        user_id = session["user_id"]
        was_done = db.execute(
            "SELECT completed FROM progress WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        ).fetchone()
        already_completed = bool(was_done and was_done["completed"])

        db.execute(
            """
            INSERT INTO progress (user_id, lesson_id, completed, quiz_score, total_questions)
            VALUES (?, ?, 1, 0, 0)
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                completed = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, lesson_id),
        )
        db.commit()
        xp_gain = 0
        if not already_completed:
            lesson = lesson_index[lang].get(lesson_id)
            xp_gain = 40
            if lesson:
                xp_gain = max(40, int(lesson.get("xp_reward", 100)) // 2)
            touch_streak(db, user_id)
            add_xp(db, user_id, xp_gain)
        return redirect(url_for("dashboard", lang=lang))

    @app.route("/bookmark/<lesson_id>", methods=["POST"])
    @login_required
    def bookmark_lesson(lesson_id: str):
        lang = get_lang()
        if lesson_id not in lesson_index[lang]:
            return redirect(url_for("dashboard", lang=lang))
        db = get_db()
        toggle_bookmark(db, session["user_id"], lesson_id)
        next_page = request.form.get("next", "dashboard")
        if next_page == "lesson":
            return redirect(url_for("lesson_detail", lesson_id=lesson_id, lang=lang))
        return redirect(url_for("dashboard", lang=lang))

    @app.route("/notes/<lesson_id>", methods=["POST"])
    @login_required
    def save_lesson_note(lesson_id: str):
        lang = get_lang()
        if lesson_id not in lesson_index[lang]:
            return redirect(url_for("dashboard", lang=lang))
        content = request.form.get("content", "")
        db = get_db()
        save_note(db, session["user_id"], lesson_id, content)
        return redirect(
            url_for(
                "lesson_detail",
                lesson_id=lesson_id,
                lang=lang,
                notes_saved=1,
            )
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
