const API = "https://toopsoob.onrender.com";

let chart = null;
let userData = null;

async function loadStats() {
    const tg = window.Telegram?.WebApp;
    const user = tg?.initDataUnsafe?.user;
    const userId = user?.id;

    if (!userId) {
        fetchData(5423348915); // ← ваш ID
        return;
    }
    fetchData(userId);
}

async function fetchData(userId) {
    try {
        const res = await fetch(`${API}/user/${userId}`);
        userData = await res.json();

        if (userData.error) return;

        // Профиль
        document.getElementById("ms-avatar").src = userData.avatar || "as.png";
        document.getElementById("ms-name").textContent = userData.name;

        // Карточки
        const weekTotal = userData.week.reduce((sum, d) => sum + d.count, 0);
        document.getElementById("ms-today").textContent = userData.today;
        document.getElementById("ms-week").textContent = weekTotal;
        document.getElementById("ms-total").textContent = userData.total;

        setPeriod("week");

    } catch (err) {
        console.error("Ошибка загрузки статистики:", err);
    }
}

function setPeriod(period) {
    if (!userData) return;

    document.getElementById("btn-week").classList.toggle("active", period === "week");
    document.getElementById("btn-day").classList.toggle("active", period === "day");

    if (period === "week") {
        const labels = userData.week.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString("ru-RU", { weekday: "short", day: "numeric" });
        });
        const values = userData.week.map(d => d.count);
        renderChart(labels, values, "Сообщений за неделю");
    } else {
        const today = new Date().toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long" });
        renderChart([today], [userData.today], "Сообщений сегодня");
    }
}

function renderChart(labels, values, label) {
    const ctx = document.getElementById("statsChart").getContext("2d");
    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label,
                data: values,
                borderColor: "#00ffcc",
                backgroundColor: "rgba(0, 255, 204, 0.08)",
                borderWidth: 2,
                pointBackgroundColor: "#00ffcc",
                pointRadius: 5,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#1a1a22",
                    titleColor: "#00ffcc",
                    bodyColor: "#fff",
                    borderColor: "#00ffcc",
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    ticks: { color: "#888", font: { family: "Fira Code" } },
                    grid: { color: "#1a1a22" }
                },
                y: {
                    ticks: { color: "#888", font: { family: "Fira Code" } },
                    grid: { color: "#1a1a22" },
                    beginAtZero: true
                }
            }
        }
    });
}

const items = document.querySelectorAll(".nav__item");
items.forEach(item => {
    item.addEventListener("click", () => {
        items.forEach(el => el.classList.remove("active"));
        item.classList.add("active");
    });
});

loadStats();