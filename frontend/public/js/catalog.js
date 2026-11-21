// קטלוג הציוד: קריאה מבסיס הנתונים דרך GET /api/items (בקשה של אורי)
import { request, escapeHtml } from "./api.js";

const list = document.getElementById("catalog-items");
const search = document.getElementById("catalog-search");
const category = document.getElementById("catalog-category");

function render(items) {
  if (!items.length) {
    list.innerHTML = `<p class="muted">לא נמצאו פריטים מתאימים.</p>`;
    return;
  }
  list.innerHTML = items
    .map((it) => {
      const n = it.available_units;
      const avail = n === 0
        ? `<span class="avail none">לא זמין כרגע</span>`
        : `<span class="avail">${n === 1 ? "יחידה אחת זמינה" : `${n} יחידות זמינות`}</span>`;
      return `<article class="item">
        <span class="tag">${escapeHtml(it.category)}</span>
        <h3>${escapeHtml(it.name)}</h3>
        <span class="muted">${escapeHtml(it.description)}</span>
        <span>פיקדון: ₪${it.deposit_amount} · עד ${it.max_loan_days} ימים</span>
        ${avail}
      </article>`;
    })
    .join("");
}

async function load() {
  const params = new URLSearchParams();
  if (category.value) params.set("category", category.value);
  if (search.value.trim()) params.set("q", search.value.trim());
  try {
    render(await request(`/items?${params}`));
  } catch (e) {
    list.innerHTML = `<p class="error">לא הצלחנו לטעון את הקטלוג: ${escapeHtml(e.message)}</p>`;
  }
}

async function init() {
  try {
    const cats = await request("/categories");
    category.insertAdjacentHTML("beforeend", cats.map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join(""));
  } catch {
    /* אם הקטגוריות לא נטענו, עדיין אפשר לחפש */
  }
  let timer;
  search.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(load, 300);
  });
  category.addEventListener("change", load);
  load();
}

init();
