// כרטיס פריט מפורט (AB#103): גלריה, פיקדון, תקופת השאלה וזמינות לפי נקודות
import { request, escapeHtml } from "./api.js";

const box = document.getElementById("item");
const id = new URLSearchParams(location.search).get("id");

function gallery(images, name) {
  if (!images.length) return `<div class="muted">אין תמונות לפריט</div>`;
  return `<div>
    <img class="main-img" id="main-img" src="${escapeHtml(images[0])}" alt="${escapeHtml(name)}" />
    <div class="thumbs">${images
      .map((src, i) => `<button type="button" aria-pressed="${i === 0}" data-src="${escapeHtml(src)}" aria-label="תמונה ${i + 1}">
        <img src="${escapeHtml(src)}" alt="" /></button>`)
      .join("")}</div>
  </div>`;
}

function render(it) {
  document.title = `${it.name} – GemachHub`;
  const rows = it.availability.length
    ? it.availability
        .map((a) => `<tr><td>${escapeHtml(a.point)}</td><td>${escapeHtml(a.address)}</td>
          <td>${a.available ? `<span class="avail">${a.available === 1 ? "יחידה אחת זמינה" : `${a.available} יחידות זמינות`}</span>` : `<span class="avail none">לא זמין</span>`}</td></tr>`)
        .join("")
    : `<tr><td colspan="3" class="muted">אין יחידות של הפריט בנקודות</td></tr>`;
  box.innerHTML = `<div class="gallery">
      ${gallery(it.images, it.name)}
      <div>
        <span class="tag">${escapeHtml(it.category)}</span>
        <h1>${escapeHtml(it.name)}</h1>
        <p>${escapeHtml(it.description)}</p>
        <div class="facts">
          <span class="fact" id="deposit">פיקדון: ₪${it.deposit_amount}</span>
          <span class="fact" id="max-days">תקופת השאלה מקסימלית: ${it.max_loan_days} ימים</span>
        </div>
      </div>
    </div>
    <h2>זמינות לפי נקודות</h2>
    <table class="table" id="availability"><thead><tr><th>נקודה</th><th>כתובת</th><th>זמינות</th></tr></thead><tbody>${rows}</tbody></table>`;
  box.querySelectorAll(".thumbs button").forEach((b) =>
    b.addEventListener("click", () => {
      document.getElementById("main-img").src = b.dataset.src;
      box.querySelectorAll(".thumbs button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    })
  );
}

async function load() {
  if (!id) {
    box.innerHTML = `<p class="error">לא נבחר פריט.</p>`;
    return;
  }
  try {
    render(await request(`/items/${encodeURIComponent(id)}`));
  } catch (e) {
    box.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

load();
