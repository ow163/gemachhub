// מסך הפתיחה: בדיקת חיבור מקצה לקצה ומפת נקודות הגמ"ח (AB#55).
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

// ממיר קואורדינטות לנקודה על המפה (מזרח משמאל לימין כמו במפה רגילה)
function project(points, w, h, pad) {
  const lats = points.map((p) => p.lat), lngs = points.map((p) => p.lng);
  const [minLat, maxLat, minLng, maxLng] = [Math.min(...lats), Math.max(...lats), Math.min(...lngs), Math.max(...lngs)];
  const sx = (w - 2 * pad) / (maxLng - minLng || 1), sy = (h - 2 * pad) / (maxLat - minLat || 1);
  return (p) => ({ x: pad + (p.lng - minLng) * sx, y: pad + (maxLat - p.lat) * sy });
}

function navLinks(p) {
  const q = encodeURIComponent(p.address);
  return `<a href="https://www.google.com/maps/dir/?api=1&destination=${q}" target="_blank" rel="noopener">ניווט ב-Google Maps</a>
          · <a href="https://waze.com/ul?q=${q}&navigate=yes" target="_blank" rel="noopener">ניווט ב-Waze</a>`;
}

function showDetails(p) {
  const box = document.getElementById("point-details");
  box.innerHTML = `<strong>${escapeHtml(p.name)}</strong>
    <span>${escapeHtml(p.address)}</span>
    <span class="muted">שעות פעילות: ${escapeHtml(p.opening_hours)}</span>
    <span>${navLinks(p)}</span>`;
  document.querySelectorAll("[data-point-id]").forEach((el) => el.classList.toggle("selected", el.dataset.pointId === String(p.id)));
}

async function showPoints() {
  const list = document.getElementById("points-list");
  const map = document.getElementById("points-map");
  try {
    // ה-API מחזיר רק נקודות פעילות
    const points = await request("/points");
    const located = points.filter((p) => p.lat != null && p.lng != null);
    if (located.length) {
      const W = 320, H = 220, toXY = project(located, W, H, 30);
      map.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="מפת נקודות הגמ&quot;ח בירושלים">
        <rect width="${W}" height="${H}" rx="12" class="map-bg"/>
        ${located.map((p) => {
          const { x, y } = toXY(p);
          return `<g class="pin" data-point-id="${p.id}" tabindex="0" role="button" aria-label="${escapeHtml(p.name)}">
            <circle cx="${x}" cy="${y}" r="9"/><text x="${x}" y="${y - 14}" text-anchor="middle">${escapeHtml(p.neighborhood)}</text></g>`;
        }).join("")}
      </svg>`;
    }
    list.innerHTML = points
      .map(
        (p) => `<li data-point-id="${p.id}" tabindex="0">
          <strong>${escapeHtml(p.name)}</strong>
          <span>${escapeHtml(p.address)}</span>
          <span class="muted">שעות פעילות: ${escapeHtml(p.opening_hours)}</span>
        </li>`
      )
      .join("");
    const byId = new Map(points.map((p) => [String(p.id), p]));
    document.querySelectorAll("[data-point-id]").forEach((el) => {
      const open = () => showDetails(byId.get(el.dataset.pointId));
      el.addEventListener("click", open);
      el.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), open()));
    });
  } catch (e) {
    list.innerHTML = `<li class="error">לא הצלחנו לטעון את הנקודות: ${escapeHtml(e.message)}</li>`;
  }
}

showHealth();
showPoints();
