// לוח בקרה (KPI) למנהל הרשת (AB#300): המדדים מתעדכנים פעם ביום, עם סינון לפי נקודה
import { request, escapeHtml } from "./api.js";

const pointSel = document.getElementById("kpi-point");
const cards = document.getElementById("kpi-cards");
const meta = document.getElementById("kpi-meta");

const KPIS = [
  ["active_loans", "השאלות פעילות"],
  ["overdue_loans", "השאלות באיחור", true],
  ["reserved_orders", "הזמנות שממתינות לאיסוף"],
  ["loans_last_30_days", "השאלות ב-30 הימים האחרונים"],
  ["units_available", "יחידות זמינות"],
  ["units_in_repair", "יחידות בתיקון", true],
  ["pending_donations", "תרומות ממתינות"],
  ["utilization_pct", "ניצול הציוד (%)"],
];

async function load() {
  const started = performance.now();
  try {
    const res = await request(`/admin/kpi?point_id=${pointSel.value}`);
    cards.innerHTML = KPIS.map(([key, label, alert]) => {
      const v = res.data[key] ?? 0;
      return `<div class="kpi${alert && v > 0 ? " alert" : ""}" data-kpi="${key}"><div class="num">${v}</div><div>${label}</div></div>`;
    }).join("");
    const ms = Math.round(performance.now() - started);
    meta.textContent = `נתונים ליום ${res.day.split("-").reverse().join("/")} · נטען תוך ${ms} מילישניות`;
    meta.dataset.ms = ms;
  } catch (e) {
    cards.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

request("/points")
  .then((points) => {
    pointSel.insertAdjacentHTML("beforeend", points.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join(""));
    pointSel.addEventListener("change", load);
    load();
  })
  .catch((e) => (cards.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`));
