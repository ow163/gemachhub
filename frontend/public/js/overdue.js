// השאלות באיחור בנקודה (AB#215): ממוין לפי ימי האיחור, כולל טלפון ופריטים
import { request, escapeHtml } from "./api.js";

const pointSel = document.getElementById("od-point");
const tbody = document.querySelector("#od-table tbody");
const count = document.getElementById("od-count");
const fmt = (d) => d.split("-").reverse().join("/");

async function load() {
  try {
    const rows = await request(`/points/${pointSel.value}/overdue`);
    count.textContent = rows.length ? `${rows.length} השאלות באיחור, נכון להיום` : "";
    tbody.innerHTML = rows.length
      ? rows
          .map((r) => `<tr data-code="${escapeHtml(r.code)}"><td>${escapeHtml(r.code)}</td><td>${escapeHtml(r.borrower_name)}</td>
            <td><a href="tel:${escapeHtml(r.phone)}">${escapeHtml(r.phone)}</a></td>
            <td>${r.items.map((i) => `${escapeHtml(i.item)} × ${i.qty}`).join("<br>")}</td>
            <td>${fmt(r.end_date)}</td><td class="days-late"><strong>${r.days_late}</strong></td></tr>`)
          .join("")
      : `<tr><td colspan="6" class="muted">אין השאלות באיחור בנקודה הזו 🎉</td></tr>`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="error">${escapeHtml(e.message)}</td></tr>`;
  }
}

request("/points")
  .then((points) => {
    pointSel.innerHTML = points.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
    pointSel.addEventListener("change", load);
    load();
  })
  .catch((e) => (tbody.innerHTML = `<tr><td colspan="6" class="error">${escapeHtml(e.message)}</td></tr>`));
