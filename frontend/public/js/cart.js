// העגלה שלי (AB#109) ויצירת הזמנה עם נקודה, תאריכים ושעת איסוף (AB#114)
import { request, escapeHtml } from "./api.js";
import { getPhone, setPhone } from "./session.js";

const loginForm = document.getElementById("login-form");
const loginState = document.getElementById("login-state");
const box = document.getElementById("cart-box");
const tbody = document.querySelector("#cart-table tbody");
const total = document.getElementById("cart-total");
const cartMsg = document.getElementById("cart-msg");
const orderCard = document.getElementById("order-card");
const orderForm = document.getElementById("order-form");
const orderMsg = document.getElementById("order-msg");
let points = [];

function renderCart(cart) {
  box.hidden = false;
  orderCard.hidden = cart.items.length === 0;
  total.textContent = `₪${cart.deposit_total}`;
  tbody.innerHTML = cart.items.length
    ? cart.items
        .map((it) => `<tr data-item-id="${it.item_id}">
          <td>${escapeHtml(it.name)}<div class="muted">עד ${it.max_loan_days} ימים</div></td>
          <td><input class="qty" type="number" min="1" max="${it.available_units}" value="${it.qty}" aria-label="כמות של ${escapeHtml(it.name)}" /></td>
          <td>₪${it.deposit_amount}</td>
          <td><button type="button" class="link-btn" data-remove>הסרה</button></td>
        </tr>`)
        .join("")
    : `<tr><td colspan="4" class="muted">העגלה ריקה. אפשר להוסיף פריטים מ<a href="/">הקטלוג</a>.</td></tr>`;
}

async function setQty(itemId, qty) {
  cartMsg.className = "";
  cartMsg.textContent = "";
  try {
    renderCart(await request("/cart", { method: "PUT", body: JSON.stringify({ phone: getPhone(), item_id: itemId, qty }) }));
  } catch (e) {
    cartMsg.className = "error";
    cartMsg.textContent = e.message;
    loadCart();
  }
}

async function loadCart() {
  renderCart(await request(`/cart?phone=${encodeURIComponent(getPhone())}`));
}

// שעות איסוף לפי שעות הפעילות של הנקודה, כל חצי שעה
function fillHours() {
  const p = points.find((x) => String(x.id) === orderForm.elements.point_id.value);
  const sel = orderForm.elements.pickup_time;
  if (!p) return (sel.innerHTML = "");
  const [oh, om] = p.open_time.split(":").map(Number), [ch, cm] = p.close_time.split(":").map(Number);
  const opts = [];
  for (let m = oh * 60 + om; m < ch * 60 + cm; m += 30) {
    const t = `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
    opts.push(`<option value="${t}">${t}</option>`);
  }
  sel.innerHTML = opts.join("");
}

async function start(phone) {
  setPhone(phone);
  loginForm.elements.phone.value = phone;
  loginState.textContent = `מחובר עם ${phone}`;
  const add = new URLSearchParams(location.search).get("add");
  if (add) {
    history.replaceState(null, "", "/cart.html");
    const cart = await request(`/cart?phone=${encodeURIComponent(phone)}`);
    const current = cart.items.find((i) => String(i.item_id) === add);
    await setQty(Number(add), (current?.qty || 0) + 1);
  } else {
    await loadCart();
  }
}

loginForm.addEventListener("submit", (e) => {
  e.preventDefault();
  start(loginForm.elements.phone.value.trim()).catch((err) => (loginState.textContent = err.message));
});

tbody.addEventListener("change", (e) => {
  if (!e.target.classList.contains("qty")) return;
  const row = e.target.closest("tr");
  setQty(Number(row.dataset.itemId), Number(e.target.value));
});
tbody.addEventListener("click", (e) => {
  if (!e.target.matches("[data-remove]")) return;
  setQty(Number(e.target.closest("tr").dataset.itemId), 0);
});

orderForm.elements.point_id.addEventListener("change", fillHours);
orderForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(orderForm));
  data.phone = getPhone();
  orderMsg.className = "";
  orderMsg.textContent = "שולח…";
  try {
    const res = await request("/orders", { method: "POST", body: JSON.stringify(data) });
    orderMsg.className = "";
    orderMsg.innerHTML = `<div class="confirm" id="order-confirm">ההזמנה התקבלה! מספר ההזמנה:
      <div class="code">${escapeHtml(res.code)}</div>
      פיקדון לתשלום באיסוף: ₪${res.deposit_total}. אפשר לראות אותה ב<a href="/loans.html">ההשאלות שלי</a>.</div>`;
    orderForm.reset();
    fillHours();
    loadCart();
  } catch (err) {
    orderMsg.className = "error";
    orderMsg.textContent = err.message;
  }
});

async function init() {
  points = await request("/points");
  orderForm.elements.point_id.innerHTML = points.map((p) => `<option value="${p.id}">${escapeHtml(p.name)} (${escapeHtml(p.opening_hours)})</option>`).join("");
  fillHours();
  const today = new Date().toISOString().slice(0, 10);
  orderForm.elements.start_date.min = today;
  orderForm.elements.end_date.min = today;
  const phone = getPhone();
  if (phone) await start(phone);
  else loginState.textContent = "הכניסו מספר טלפון כדי לראות את העגלה שלכם. העגלה נשמרת גם לכניסה הבאה.";
}

init().catch((e) => (loginState.textContent = e.message));
