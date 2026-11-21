// מסך הפתיחה: בדיקת חיבור מקצה לקצה ורשימת נקודות הגמ"ח.
import { request, escapeHtml } from "./api.js";

async function showHealth() {
  const badge = document.getElementById("health");
  const text = badge.querySelector(".text");
  try {
    await request("/health");
    badge.className = "badge badge-ok";
    text.textContent = "מחובר לשרת ולבסיס הנתונים";
  } catch {
    badge.className = "badge badge-error";
    text.textContent = "אין חיבור לשרת או לבסיס הנתונים";
  }
}

async function showPoints() {
  const list = document.getElementById("points-list");
  try {
    const points = await request("/points");
    list.innerHTML = points
      .map(
        (p) => `<li>
          <strong>${escapeHtml(p.name)}</strong>
          <span>${escapeHtml(p.address)}</span>
          <span class="muted">שעות פעילות: ${escapeHtml(p.opening_hours)}</span>
        </li>`
      )
      .join("");
  } catch (e) {
    list.innerHTML = `<li class="error">לא הצלחנו לטעון את הנקודות: ${escapeHtml(e.message)}</li>`;
  }
}

showHealth();
showPoints();
