# Nginx reverse proxy image
# Routes traffic to Django backend and React frontend
FROM nginx:1.25-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
