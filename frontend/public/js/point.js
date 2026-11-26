// עמדת מתנדב: איסופים להיום (AB#173) ומסירת הזמנה לפי קוד, סריקת QR או טלפון (AB#178)
import { request, escapeHtml } from "./api.js";

export const pointSel = document.getElementById("pt-point");
const pkBody = document.querySelector("#pk-table tbody");
const hoForm = document.getElementById("ho-form");
const hoResult = document.getElementById("ho-result");
const scanBtn = document.getElementById("ho-scan");
const video = document.getElementById("ho-video");
const fmt = (d) => d.split("-").reverse().join("/");
const itemsText = (items) => items.map((i) => `${escapeHtml(i.item)} × ${i.qty}`).join("<br>");

export async function loadPickups() {
  try {
    const data = await request(`/points/${pointSel.value}/pickups`);
    pkBody.innerHTML = data.pickups.length
      ? data.pickups
          .map((o) => `<tr data-code="${escapeHtml(o.code)}"><td>${o.pickup_time}</td><td>${escapeHtml(o.code)}</td>
            <td>${escapeHtml(o.borrower_name)}<div class="muted">${escapeHtml(o.phone)}</div></td>
            <td>${itemsText(o.items)}</td>
            <td><span class="badge-st${o.collected ? " done" : ""}">${o.collected ? "נאסף ✓" : "ממתין"}</span></td></tr>`)
          .join("")
      : `<tr><td colspan="5" class="muted">אין איסופים היום בנקודה הזו.</td></tr>`;
  } catch (e) {
    pkBody.innerHTML = `<tr><td colspan="5" class="error">${escapeHtml(e.message)}</td></tr>`;
  }
}

function orderHtml(o) {
  const deposit = o.deposit_ok
    ? `<span class="deposit-ok">פיקדון ₪${o.deposit_total} בתוקף ✓</span>`
    : `<span class="deposit-bad">אין פיקדון בתוקף</span>`;
  const action = o.status === "reserved"
    ? `<button type="button" data-handover="${o.id}">מסירת הציוד</button>`
    : `<span class="badge-st done">כבר נמסר</span>`;
  return `<div class="order-box" data-order="${escapeHtml(o.code)}">
    <div><strong>${escapeHtml(o.code)}</strong> · ${escapeHtml(o.borrower_name)} · ${escapeHtml(o.phone)}</div>
    <div>איסוף ${fmt(o.start_date)} ${o.pickup_time} · החזרה עד ${fmt(o.end_date)}</div>
    <div>${o.items.map((i) => `${escapeHtml(i.item)} × ${i.qty} <span class="muted">(${i.codes.map(escapeHtml).join(", ")})</span>`).join("<br>")}</div>
    ${deposit}
    <div>${action}</div>
  </div>`;
}

async function lookup(query) {
  const q = query.trim();
  const isCode = /^gh-/i.test(q);
  const params = new URLSearchParams({ point_id: pointSel.value, [isCode ? "code" : "phone"]: q });
  hoResult.innerHTML = `<p class="muted">מחפש…</p>`;
  try {
    const orders = await request(`/orders/lookup?${params}`);
    hoResult.innerHTML = orders.map(orderHtml).join("");
  } catch (e) {
    hoResult.innerHTML = `<p class="error" id="ho-error">${escapeHtml(e.message)}</p>`;
  }
}

hoForm.addEventListener("submit", (e) => {
  e.preventDefault();
  lookup(hoForm.elements.query.value);
});

hoResult.addEventListener("click", async (e) => {
  const id = e.target.dataset.handover;
  if (!id) return;
  e.target.disabled = true;
  try {
    const res = await request(`/orders/${id}/handover`, { method: "POST", body: JSON.stringify({ point_id: Number(pointSel.value) }) });
    e.target.replaceWith(Object.assign(document.createElement("span"), { className: "success", textContent: `נמסר! ${res.units} יחידות סומנו כמושאלות.` }));
    loadPickups();
  } catch (err) {
    e.target.disabled = false;
    e.target.insertAdjacentHTML("afterend", `<p class="error">${escapeHtml(err.message)}</p>`);
  }
});

// סריקת QR במצלמה, בדפדפנים שתומכים ב-BarcodeDetector (כרום באנדרואיד). אחרת מקלידים את הקוד.
if ("BarcodeDetector" in window) {
  scanBtn.hidden = false;
  scanBtn.addEventListener("click", async () => {
    const detector = new window.BarcodeDetector({ formats: ["qr_code"] });
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    video.srcObject = stream;
    video.hidden = false;
    await video.play();
    const tick = async () => {
      const [code] = await detector.detect(video).catch(() => []);
      if (code) {
        stream.getTracks().forEach((t) => t.stop());
        video.hidden = true;
        hoForm.elements.query.value = code.rawValue;
        lookup(code.rawValue);
      } else requestAnimationFrame(tick);
    };
    tick();
  });
}

const points = await request("/points");
pointSel.innerHTML = points.map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
pointSel.addEventListener("change", () => {
  hoResult.innerHTML = "";
  loadPickups();
});
loadPickups();
