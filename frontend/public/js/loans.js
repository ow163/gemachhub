// ההשאלות שלי (AB#151): פעילות והיסטוריה, ממוינות לפי תאריך החזרה, איחור מסומן באדום
import { request, escapeHtml } from "./api.js";
import { getPhone, setPhone } from "./session.js";
import { qrSvg } from "./qr.js";

const form = document.getElementById("loans-form");
const list = document.getElementById("loans-list");
const fmt = (d) => d.split("-").reverse().join("/");

async function load(phone) {
  setPhone(phone);
  try {
    const rows = await request(`/loans?phone=${encodeURIComponent(phone)}`);
    list.innerHTML = rows.length
      ? rows
          .map((l) => `<article class="loan${l.is_overdue ? " overdue" : ""}" data-code="${escapeHtml(l.code)}">
            <div><strong>${escapeHtml(l.code)}</strong> · <span class="status">${escapeHtml(l.status_text)}${l.is_overdue ? ` (${l.days_late} ימים)` : ""}</span></div>
            <div>${l.items.map((i) => `${escapeHtml(i.item)} × ${i.qty}`).join(", ")}</div>
            <div>איסוף ${fmt(l.start_date)} בשעה ${l.pickup_time} · החזרה עד <strong>${fmt(l.end_date)}</strong></div>
            <div class="muted">${escapeHtml(l.point)} · ${escapeHtml(l.point_address)} · ${escapeHtml(l.point_hours)}</div>
            ${["reserved", "picked_up"].includes(l.status) ? `<div class="qr">${qrSvg(l.code)}<span class="muted">קוד לסריקה בנקודה</span></div>` : ""}
          </article>`)
          .join("")
      : `<p class="muted">אין השאלות למספר הזה.</p>`;
  } catch (e) {
    list.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  load(form.elements.phone.value.trim());
});

const saved = getPhone();
if (saved) {
  form.elements.phone.value = saved;
  load(saved);
}
