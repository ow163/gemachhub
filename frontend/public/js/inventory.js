// מלאי הנקודה (AB#236): יחידות לפי סטטוס, עם סינון לפי פריט
import { request, escapeHtml } from "./api.js";

const pointSel = document.getElementById("inv-point");
const itemSel = document.getElementById("inv-item");
const summary = document.getElementById("inv-summary");
const tbody = document.querySelector("#inv-table tbody");
const LABELS = { available: "זמין", loaned: "מושאל", repair: "בתיקון", lost: "אבד" };

async function load() {
  const params = new URLSearchParams();
  if (itemSel.value) params.set("item_id", itemSel.value);
  try {
    const data = await request(`/points/${pointSel.value}/inventory?${params}`);
    summary.innerHTML = Object.entries(LABELS)
      .map(([k, label]) => `<span class="chip st-${k}" data-status="${k}">${label}: ${data.summary[k] ?? 0}</span>`)
      .join("");
    tbody.innerHTML = data.units.length
      ? data.units
          .map((u) => `<tr><td>${escapeHtml(u.code)}</td><td>${escapeHtml(u.item)}</td>
            <td class="st-${u.status}">${escapeHtml(u.status_text)}</td></tr>`)
          .join("")
      : `<tr><td colspan="3" class="muted">אין יחידות להצגה</td></tr>`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="3" class="error">${escapeHtml(e.message)}</td></tr>`;
  }
}

async function init() {
  const [points, items] = await Promise.all([request("/points"), request("/items")]);
  pointSel.innerHTML = points.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
  itemSel.insertAdjacentHTML("beforeend", items.map((i) => `<option value="${i.id}">${escapeHtml(i.name)}</option>`).join(""));
  const fromUrl = new URLSearchParams(location.search).get("point");
  if (fromUrl) pointSel.value = fromUrl;
  pointSel.addEventListener("change", load);
  itemSel.addEventListener("change", load);
  load();
}

init().catch((e) => (tbody.innerHTML = `<tr><td colspan="3" class="error">${escapeHtml(e.message)}</td></tr>`));
