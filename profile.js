const API = "https://toopsoob.onrender.com/top"; // ← заменить на Railway URL после деплоя

async function loadProfile() {
    // Получаем user_id из Telegram Mini App
    const tg = window.Telegram?.WebApp;
    const user = tg?.initDataUnsafe?.user;
    const userId = user?.id;

    if (!userId) {
        // Для теста в браузере — подставь свой user_id
        console.warn("Нет Telegram user_id, используется тестовый");
        loadData(5423348915); // ← вставь свой Telegram ID для теста
        return;
    }

    loadData(userId);
}

async function loadData(userId) {
    try {
        const res = await fetch(`${API}/user/${userId}`);
        const u = await res.json();

        if (u.error) {
            document.getElementById("prof-name").textContent = "Не найден";
            return;
        }

        document.getElementById("prof-avatar").src = u.avatar || "as.png";
        document.getElementById("prof-name").textContent = u.name;
        document.getElementById("prof-username").textContent = u.username ? `@${u.username}` : "";
        document.getElementById("prof-rank").textContent = `#${u.rank}`;
        document.getElementById("prof-total").textContent = u.total;
        document.getElementById("prof-today").textContent = u.today;

    } catch (err) {
        console.error("Ошибка загрузки профиля:", err);
    }
}

// Nav active
const items = document.querySelectorAll(".nav__item");
items.forEach(item => {
    item.addEventListener("click", () => {
        items.forEach(el => el.classList.remove("active"));
        item.classList.add("active");
    });
});

loadProfile();
