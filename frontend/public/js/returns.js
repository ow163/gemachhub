// קליטת החזרה (AB#194) ותיעוד נזק (AB#204) בעמדת המתנדב
import { request, escapeHtml } from "./api.js";

const pointSel = document.getElementById("pt-point");
const form = document.getElementById("rt-form");
const box = document.getElementById("rt-order");
const dialog = document.getElementById("damage-dialog");
const dmForm = document.getElementById("damage-form");
const dmMsg = document.getElementById("dm-msg");
let order = null;

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

function render() {
  const units = order.items.flatMap((i) => i.codes.map((code) => ({ code, item: i.item })));
  box.innerHTML = `<div class="order-box" data-order="${escapeHtml(order.code)}">
    <div><strong>${escapeHtml(order.code)}</strong> · ${escapeHtml(order.borrower_name)} · ${escapeHtml(order.phone)}</div>
    <form class="inline-form" id="scan-form">
      <label class="grow">סריקת יחידה<input name="unit" placeholder="קוד היחידה, למשל KY-TBL-03" autocomplete="off" /></label>
      <button type="submit" class="secondary">סימון</button>
    </form>
    <ul class="units-list">${units
      .map((u) => `<li data-code="${escapeHtml(u.code)}">
        <label><input type="checkbox" value="${escapeHtml(u.code)}" /> ${escapeHtml(u.code)} · ${escapeHtml(u.item)}</label>
        <button type="button" class="link-btn" data-damage="${escapeHtml(u.code)}">דיווח נזק</button>
      </li>`)
      .join("")}</ul>
    <button type="button" id="rt-submit">קליטת היחידות שסומנו</button>
    <p id="rt-msg" role="status" aria-live="polite"></p>
  </div>`;
}

async function loadOrder(code) {
  box.innerHTML = `<p class="muted">טוען…</p>`;
  try {
    const [o] = await request(`/orders/lookup?${new URLSearchParams({ point_id: pointSel.value, code })}`);
    if (o.status !== "picked_up") throw new Error(o.status === "reserved" ? "ההזמנה עוד לא נמסרה" : "ההזמנה כבר הוחזרה");
    order = o;
    render();
  } catch (e) {
    order = null;
    box.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  loadOrder(form.elements.code.value.trim());
});

box.addEventListener("submit", (e) => {
  if (e.target.id !== "scan-form") return;
  e.preventDefault();
  const input = e.target.elements.unit;
  const cb = box.querySelector(`input[type=checkbox][value="${CSS.escape(input.value.trim().toUpperCase())}"]`);
  if (cb) cb.checked = true;
  input.value = "";
  input.focus();
});

box.addEventListener("click", async (e) => {
  if (e.target.dataset.damage) {
    dmForm.reset();
    dmMsg.textContent = "";
    document.getElementById("dm-code").textContent = e.target.dataset.damage;
    dialog.dataset.code = e.target.dataset.damage;
    dialog.showModal();
    return;
  }
  if (e.target.id !== "rt-submit") return;
  const codes = [...box.querySelectorAll("input[type=checkbox]:checked")].map((c) => c.value);
  const msg = document.getElementById("rt-msg");
  try {
    const res = await request(`/orders/${order.id}/return`, {
      method: "POST",
      body: JSON.stringify({ point_id: Number(pointSel.value), unit_codes: codes }),
    });
    codes.forEach((c) => box.querySelector(`li[data-code="${CSS.escape(c)}"]`)?.classList.add("returned"));
    msg.className = "success";
    msg.textContent = res.order_status === "returned"
      ? res.deposit_status === "released" ? "כל הציוד הוחזר תקין. מסגרת הפיקדון שוחררה." : "כל הציוד הוחזר. נרשם נזק, הפיקדון נשאר תפוס לבדיקה."
      : `נקלטו ${res.returned_now} יחידות. נשארו ${res.remaining} להחזרה.`;
  } catch (err) {
    msg.className = "error";
    msg.textContent = err.message;
  }
});

document.getElementById("dm-cancel").addEventListener("click", () => dialog.close());
dmForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(dmForm));
  try {
    const photo = await readPhoto(data.photo_file);
    const res = await request(`/units/${encodeURIComponent(dialog.dataset.code)}/damage`, {
      method: "POST",
      body: JSON.stringify({ severity: data.severity, description: data.description, photo }),
    });
    dialog.close();
    const li = box.querySelector(`li[data-code="${CSS.escape(res.code)}"]`);
    li?.insertAdjacentHTML("beforeend", `<span class="st-repair">נזק ${escapeHtml(res.severity_text)} · עברה לתיקון</span>`);
  } catch (err) {
    dmMsg.className = "error";
    dmMsg.textContent = err.message;
  }
});
