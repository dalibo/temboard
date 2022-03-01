FROM python:3.7-slim

RUN set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        git-core \
        postgresql-client \
        sudo \
    ; \
    rm -rf /var/lib/apt/lists/* ; \
    apt-get clean ; \
    :

RUN git clone --depth=1 --recursive https://github.com/dalibo/temboard/ && \
    pip install --no-cache-dir ./temboard psycopg2-binary && \
    rm -rf temboard

RUN set -ex; \
    python -c 'import urllib.request as u; u.urlretrieve("https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh", "/usr/local/bin/wait-for-it")' ; \
    chmod 0755 /usr/local/bin/wait-for-it ; \
    :

RUN useradd --home-dir /var/lib/temboard --create-home --system temboard
VOLUME /var/lib/temboard
WORKDIR /var/lib/temboard

RUN mkdir -p /etc/temboard \
    && chown temboard. /etc/temboard
VOLUME /etc/temboard

COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard"]

EXPOSE 8888
