# האתר הוא קבצים סטטיים (HTML, CSS, JavaScript) ש-nginx מגיש.
# nginx גם מעביר כל בקשה ל-/api לקונטיינר ה-backend.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public /usr/share/nginx/html
EXPOSE 80
