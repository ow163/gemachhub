// הצעת תרומה ומעקב סטטוס (AB#258, AB#273) - החלק של רפאל
import { request, escapeHtml } from "./api.js";

const form = document.getElementById("donate-form");
const msg = document.getElementById("donate-msg");
const recent = document.getElementById("donate-recent");

const STATUS = { pending: "ממתינה לאישור", approved: "אושרה", rejected: "נדחתה", received: "נקלטה בנקודה" };
const mineForm = document.getElementById("mine-form");
const mineList = document.getElementById("mine-list");

// קריאת התמונה שנבחרה כ-data URL כדי לשלוח אותה יחד עם הטופס
function readPhoto(file) {
  return new Promise((resolve, reject) => {
    if (!file || !file.size) return resolve("");
    if (file.size > 2 * 1024 * 1024) return reject(new Error("התמונה גדולה מדי (עד 2MB)"));
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("לא הצלחנו לקרוא את התמונה"));
    reader.readAsDataURL(file);
  });
}

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
    data.photo = await readPhoto(data.photo_file);
    delete data.photo_file;
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

mineForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const phone = mineForm.elements.phone.value.trim();
  try {
    const rows = await request(`/donations/mine?phone=${encodeURIComponent(phone)}`);
    mineList.innerHTML = rows.length
      ? rows.map((d) => `<li data-donation-id="${d.id}">פנייה #${d.id} · ${escapeHtml(d.item_name)} · ${escapeHtml(d.point)} · <strong>${escapeHtml(d.status_text)}</strong></li>`).join("")
      : `<li class="muted">לא נמצאו תרומות למספר הזה.</li>`;
  } catch (err) {
    mineList.innerHTML = `<li class="error">${escapeHtml(err.message)}</li>`;
  }
});

fillSelect("category_id", "/categories");
fillSelect("point_id", "/points");
showRecent();
