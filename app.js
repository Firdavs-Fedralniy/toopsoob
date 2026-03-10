fetch("https://toopsoob.onrender.com/top")
  .then(r => r.json())
  .then(data => {
    const root = document.getElementById("top");
    root.innerHTML = "";

    data.forEach((u, i) => {
      const div = document.createElement("div");
      div.className = "user__wrapper";

      div.innerHTML = `
        <p class="place">${i + 1}</p>
        <div class="user__img">
          <img src="${u.avatar ? u.avatar : 'as.png'}" alt="">
        </div>
        <div class="user__top">
          <b class="user__info">${u.name}</b>
          <span class="user__stats">${u.count} msgs</span>
        </div>
      `;

      root.appendChild(div);
    });
  })
  .catch(err => {
    console.error("Ошибка загрузки:", err);
  });

const items = document.querySelectorAll(".nav__item");

items.forEach(item => {
  item.addEventListener("click", () => {
    items.forEach(el => el.classList.remove("active")); // ❌ убираем у всех
    item.classList.add("active"); // ✅ ставим только на нажатый
  });
});