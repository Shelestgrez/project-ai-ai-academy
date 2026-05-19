(function () {
    const root = document.documentElement;
    const themeKey = "ai-academy-theme";

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        const btn = document.getElementById("themeToggle");
        if (btn) {
            btn.textContent = theme === "dark" ? btn.dataset.lightLabel : btn.dataset.darkLabel;
        }
    }

    const savedTheme = localStorage.getItem(themeKey);
    if (savedTheme) {
        applyTheme(savedTheme);
    }

    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) {
        themeBtn.addEventListener("click", function () {
            const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem(themeKey, next);
            applyTheme(next);
        });
    }

    const searchInput = document.getElementById("lessonSearch");
    const lessonCards = document.querySelectorAll("[data-lesson-card]");
    const filterButtons = document.querySelectorAll("[data-lesson-filter]");

    function filterLessons() {
        const query = (searchInput && searchInput.value ? searchInput.value : "").trim().toLowerCase();
        const activeFilter = document.querySelector("[data-lesson-filter].active");
        const mode = activeFilter ? activeFilter.dataset.lessonFilter : "all";

        lessonCards.forEach(function (card) {
            const title = (card.dataset.title || "").toLowerCase();
            const desc = (card.dataset.description || "").toLowerCase();
            const completed = card.dataset.completed === "1";
            const bookmarked = card.dataset.bookmarked === "1";
            const matchesQuery = !query || title.includes(query) || desc.includes(query);

            let matchesFilter = true;
            if (mode === "done") matchesFilter = completed;
            if (mode === "pending") matchesFilter = !completed;
            if (mode === "bookmarked") matchesFilter = bookmarked;

            card.classList.toggle("d-none", !(matchesQuery && matchesFilter));
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterLessons);
    }
    filterButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            filterButtons.forEach(function (b) {
                b.classList.remove("active");
            });
            btn.classList.add("active");
            filterLessons();
        });
    });

    document.querySelectorAll(".flashcard").forEach(function (card) {
        card.addEventListener("click", function () {
            card.classList.toggle("is-flipped");
        });
    });

    const lessonId = document.body.getAttribute("data-lesson-id");
    if (lessonId) {
        const storageKey = "ai-academy-steps-" + lessonId;
        let saved = [];
        try {
            saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
        } catch (e) {
            saved = [];
        }
        document.querySelectorAll("[data-step-index]").forEach(function (item) {
            const idx = item.dataset.stepIndex;
            const box = item.querySelector("input[type=checkbox]");
            if (box && saved.includes(idx)) {
                box.checked = true;
            }
            if (box) {
                box.addEventListener("change", function () {
                    const checked = [];
                    document.querySelectorAll("[data-step-index] input:checked").forEach(function (el) {
                        checked.push(el.closest("[data-step-index]").dataset.stepIndex);
                    });
                    localStorage.setItem(storageKey, JSON.stringify(checked));
                });
            }
        });
    }

    const dailyForm = document.getElementById("dailyChallenge");
    if (dailyForm) {
        dailyForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const selected = dailyForm.querySelector("input[name=daily]:checked");
            const answer = parseInt(dailyForm.dataset.answer, 10);
            const feedback = document.getElementById("dailyFeedback");
            if (!selected || !feedback) return;
            const ok = parseInt(selected.value, 10) === answer;
            feedback.classList.remove("d-none", "alert-success", "alert-danger");
            feedback.classList.add(ok ? "alert-success" : "alert-danger");
            feedback.textContent = ok ? dailyForm.dataset.ok : dailyForm.dataset.fail;
        });
    }
})();
