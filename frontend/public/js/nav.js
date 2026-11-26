// תפריט עליון משותף לכל המסכים. כל מסך חדש מוסיף כאן שורה אחת.
const PAGES = [
  { href: "/", label: "קטלוג ונקודות" },
  { href: "/cart.html", label: "העגלה שלי" },
  { href: "/loans.html", label: "ההשאלות שלי" },
  { href: "/inventory.html", label: "מלאי נקודה" },
  { href: "/overdue.html", label: "השאלות באיחור" },
];

const here = location.pathname.replace(/\/index\.html$/, "/");
const nav = document.createElement("nav");
nav.className = "topnav";
nav.setAttribute("aria-label", "ניווט ראשי");
nav.innerHTML = `<div class="topnav-inner">
  <a class="topnav-brand" href="/"><span class="logo" aria-hidden="true">ג</span>GemachHub</a>
  <ul>${PAGES.map((p) => `<li><a href="${p.href}"${p.href === here ? ' aria-current="page"' : ""}>${p.label}</a></li>`).join("")}</ul>
</div>`;
document.body.prepend(nav);
