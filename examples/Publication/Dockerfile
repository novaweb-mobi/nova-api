FROM docker.pkg.github.com/novaweb-mobi/connexion-api-docker/novaapi:3.8-alpine
COPY User.py .
COPY UserDAO.py .
COPY Publication.py .
COPY PublicationDAO.py .
ENV PORT 8080
ENV ENTITIES User, Publication
ENV DB_URL 172.18.0.2
ENV DB_USER root
ENV DB_PASSWORD root
ENV DB_NAME default
