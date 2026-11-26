// ניהול רשת: אישור או דחייה של תרומות ממתינות (AB#279). בדחייה חובה נימוק.
import { request, escapeHtml } from "./api.js";

const list = document.getElementById("da-list");

async function load() {
  try {
    const rows = await request("/admin/donations?status=pending");
    list.innerHTML = rows.length
      ? rows
          .map((d) => `<article class="donation" data-donation-id="${d.id}">
            <img src="${escapeHtml(d.photo || "/img/gemach-label.svg")}" alt="תמונת ${escapeHtml(d.item_name)}" />
            <div>
              <strong>#${d.id} · ${escapeHtml(d.item_name)}</strong> <span class="muted">${escapeHtml(d.category || "ללא קטגוריה")}</span>
              <div>${escapeHtml(d.description)}</div>
              <div class="muted">${escapeHtml(d.donor_name)} · ${escapeHtml(d.phone)} · מסירה ב${escapeHtml(d.point)}</div>
              <div class="actions">
                <button type="button" data-decide="approve">אישור</button>
                <input placeholder="נימוק (חובה בדחייה)" aria-label="נימוק" />
                <button type="button" class="danger" data-decide="reject">דחייה</button>
              </div>
              <p class="msg" role="status"></p>
            </div>
          </article>`)
          .join("")
      : `<p class="muted">אין תרומות שממתינות להחלטה.</p>`;
  } catch (e) {
    list.innerHTML = `<p class="error">${escapeHtml(e.message)}</p>`;
  }
}

list.addEventListener("click", async (e) => {
  const decision = e.target.dataset.decide;
  if (!decision) return;
  const card = e.target.closest(".donation");
  const msg = card.querySelector(".msg");
  try {
    const res = await request(`/donations/${card.dataset.donationId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, reason: card.querySelector("input").value }),
    });
    msg.className = "msg success";
    msg.textContent = `התרומה ${res.status_text}. התורם קיבל הודעה וההחלטה נרשמה ביומן.`;
    card.querySelectorAll("button, input").forEach((el) => (el.disabled = true));
  } catch (err) {
    msg.className = "msg error";
    msg.textContent = err.message;
  }
});

load();
