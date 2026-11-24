// הצעת תרומה: שליחת הצעות מתורמים דרך POST /api/donations (החלק של רפאל)
import { request, escapeHtml } from "./api.js";

const form = document.getElementById("donate-form");
const msg = document.getElementById("donate-msg");
const recent = document.getElementById("donate-recent");

const STATUS = { pending: "ממתינה לאישור", approved: "אושרה", rejected: "נדחתה", received: "התקבלה" };

async function fillSelect(name, path) {
  try {
    const rows = await request(path);
    form.elements[name].insertAdjacentHTML("beforeend", rows.map((r) => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join(""));
  } catch {
    /* אם הטעינה נכשלה, הרשימה פשוט נשארת ריקה */
  }
}

async function showRecent() {
  try {
    const rows = await request("/donations?limit=5");
    recent.innerHTML = rows.length
      ? rows.map((d) => `<li>#${d.id} · ${escapeHtml(d.item_name)} · ${escapeHtml(d.point)} · <span class="muted">${STATUS[d.status] || d.status}</span></li>`).join("")
      : `<li class="muted">עדיין אין הצעות.</li>`;
  } catch {
    recent.innerHTML = "";
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const button = form.querySelector("button");
  const data = Object.fromEntries(new FormData(form));
  button.disabled = true;
  msg.className = "";
  msg.textContent = "שולח…";
  try {
    const res = await request("/donations", { method: "POST", body: JSON.stringify(data) });
    msg.className = "success";
    msg.textContent = `תודה! ההצעה נשלחה. מספר הפנייה: #${res.id}`;
    form.reset();
    showRecent();
  } catch (err) {
    msg.className = "error";
    msg.textContent = err.message;
  } finally {
    button.disabled = false;
  }
});

fillSelect("category_id", "/categories");
fillSelect("point_id", "/points");
showRecent();
