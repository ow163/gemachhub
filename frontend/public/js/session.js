// מספר הטלפון של המשתמש נשמר בדפדפן, כדי שהעגלה וההשאלות ייטענו גם בכניסה הבאה (AB#109)
const KEY = "gh_phone";

export function getPhone() {
  try {
    return localStorage.getItem(KEY) || "";
  } catch {
    return "";
  }
}

export function setPhone(phone) {
  try {
    localStorage.setItem(KEY, phone);
  } catch {
    /* אם אין גישה לאחסון, פשוט נבקש שוב את המספר */
  }
}
