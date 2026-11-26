// קטלוג הציוד: קריאה מבסיס הנתונים דרך GET /api/items (AB#88, AB#93)
import { request, escapeHtml } from "./api.js";

const list = document.getElementById("catalog-items");
const search = document.getElementById("catalog-search");
const category = document.getElementById("catalog-category");
const timing = document.getElementById("catalog-timing");

export function cardHtml(it) {
  const n = it.available_units;
  const avail = n === 0
    ? `<span class="avail none">לא זמין כרגע</span>`
    : `<span class="avail">${n === 1 ? "יחידה אחת זמינה" : `${n} יחידות זמינות`}</span>`;
  return `<article class="item" data-item-id="${it.id}">
    <span class="tag">${escapeHtml(it.category)}</span>
    <h3>${escapeHtml(it.name)}</h3>
    <span class="muted">${escapeHtml(it.description)}</span>
    <span>פיקדון: ₪${it.deposit_amount} · עד ${it.max_loan_days} ימים</span>
    ${avail}
  </article>`;
}

function render(items) {
  if (!items.length) {
    // AB#93: כשאין תוצאות מציעים לפנות לעוזר החכם
    list.innerHTML = `<div class="empty">
      <p>לא מצאנו פריט מתאים לחיפוש.</p>
      <p class="muted">לא בטוחים מה צריך? ספרו לעוזר החכם על האירוע שלכם, והוא ימליץ על ציוד מהקטלוג.</p>
      <button type="button" class="secondary" disabled title="העוזר החכם יתווסף בגרסה הבאה">שאלו את העוזר החכם</button>
    </div>`;
    return;
  }
  list.innerHTML = items.map(cardHtml).join("");
}

async function load() {
  const params = new URLSearchParams();
  if (category.value) params.set("category", category.value);
  if (search.value.trim()) params.set("q", search.value.trim());
  const started = performance.now();
  try {
    render(await request(`/items?${params}`));
    // דרישת ביצועים (AB#88): הקטלוג נטען תוך 2 שניות לכל היותר
    const ms = Math.round(performance.now() - started);
    timing.textContent = `נטען תוך ${ms} מילישניות`;
    timing.dataset.ms = ms;
  } catch (e) {
    list.innerHTML = `<p class="error">לא הצלחנו לטעון את הקטלוג: ${escapeHtml(e.message)}</p>`;
  }
}

async function init() {
  try {
    // AB#88: ליד כל קטגוריה מוצג מספר הפריטים שבה
    const cats = await request("/categories");
    category.insertAdjacentHTML(
      "beforeend",
      cats.map((c) => `<option value="${c.id}">${escapeHtml(c.name)} (${c.item_count})</option>`).join("")
    );
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

if (list) init();
