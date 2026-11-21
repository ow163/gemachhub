// כל הקריאות לשרת עוברות דרך הקובץ הזה.
// הכתובת יחסית (/api): nginx מעביר אותה לקונטיינר ה-backend.

export async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(body?.error || `שגיאה ${res.status}`);
  }
  return body;
}

// הגנה מפני הזרקת HTML כשמציגים טקסט שהגיע מהשרת
export function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
}
