FROM docker.pkg.github.com/novaweb-mobi/connexion-api-docker/novaapi:3.8-alpine
COPY User.py .
COPY UserDAO.py .
ENV PORT 8080
ENV ENTITIES User
ENV DB_URL 172.18.0.2
ENV DB_USER root
ENV DB_PASSWORD root
ENV DB_NAME default
