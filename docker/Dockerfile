FROM python:3.8-alpine
WORKDIR /app
ENV PROCESSES 1
ENV PORT 80
ENV THREAD true
RUN apk add --virtual .build-dependencies \
            --no-cache \
            python3-dev \
            build-base \
            linux-headers \
            pcre-dev \
            pcre
RUN pip install --no-cache-dir --upgrade pip
COPY requirements-docker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt
RUN apk del .build-dependencies && rm -rf /var/cache/apk/*
COPY server-novaapi.py server.py
COPY wsgi.ini .
EXPOSE ${PORT}
CMD ["uwsgi", "--ini", "/app/wsgi.ini"]

