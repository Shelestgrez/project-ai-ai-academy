from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import Dict, List

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db_support import INTEGRITY_ERRORS, attach_database, get_db, init_schema


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "database.db")))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["DATABASE"] = str(DATABASE_PATH)
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
    attach_database(app, str(DATABASE_PATH))

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
        ],
    }

    lesson_images = {
        "intro-ai": "images/intro-ai.jpg",
        "ml-basics": "images/ml-basics.jpg",
        "neural-basics": "images/neural-basics.jpg",
        "data-foundations": "images/data-foundations.jpg",
        "ethics-safety": "images/ethics-safety.jpg",
        "gen-ai-llm": "images/gen-ai-llm.jpg",
    }

    for lang, entries in extra_lessons.items():
        lesson_catalog[lang].extend(entries)

    for lang, lessons in lesson_catalog.items():
        for lesson in lessons:
            extension = deep_lessons.get(lang, {}).get(lesson["id"])
            if extension:
                lesson.update(extension)
            lesson["image"] = lesson_images.get(lesson["id"], "images/intro-ai.jpg")

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

    @app.route("/dashboard")
    @login_required
    def dashboard():
        lang = get_lang()
        db = get_db()
        lesson_ids = [lesson["id"] for lesson in lesson_catalog[lang]]
        rows = db.execute(
            """
            SELECT lesson_id, completed, quiz_score, total_questions
            FROM progress
            WHERE user_id = ?
            """,
            (session["user_id"],),
        ).fetchall()
        progress_map = {row["lesson_id"]: row for row in rows}
        completed_count = sum(
            1
            for lesson_id in lesson_ids
            if progress_map.get(lesson_id) and bool(progress_map[lesson_id]["completed"])
        )
        progress_percent = int((completed_count / len(lesson_ids)) * 100) if lesson_ids else 0

        lessons = []
        for lesson in lesson_catalog[lang]:
            row = progress_map.get(lesson["id"])
            lessons.append(
                {
                    **lesson,
                    "completed": bool(row["completed"]) if row else False,
                    "quiz_score": int(row["quiz_score"]) if row else 0,
                    "total_questions": int(row["total_questions"]) if row else len(lesson["quiz"]),
                }
            )

        return render_template(
            "dashboard.html",
            lang=lang,
            user_name=session.get("user_name", ""),
            lessons=lessons,
            progress_percent=progress_percent,
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

        return render_template(
            "lesson.html",
            lang=lang,
            lesson=lesson,
            result_message=request.args.get("result_message", ""),
            score=score,
            total=total,
            completed=bool(saved["completed"]) if saved else False,
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
            (session["user_id"], lesson_id, 1 if passed else 0, correct, total_questions),
        )
        db.commit()

        return redirect(
            url_for(
                "lesson_detail",
                lesson_id=lesson_id,
                lang=lang,
                result_message=result_message,
            )
        )

    @app.route("/complete/<lesson_id>", methods=["POST"])
    @login_required
    def complete_lesson(lesson_id: str):
        lang = get_lang()
        db = get_db()
        db.execute(
            """
            INSERT INTO progress (user_id, lesson_id, completed, quiz_score, total_questions)
            VALUES (?, ?, 1, 0, 0)
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET
                completed = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session["user_id"], lesson_id),
        )
        db.commit()
        return redirect(url_for("dashboard", lang=lang))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
