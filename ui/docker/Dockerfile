FROM python:3.7-slim AS builder

RUN set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        git-core \
    ; \
    rm -rf /var/lib/apt/lists/* ; \
    apt-get clean ; \
    :

RUN set -ex; \
    git clone --depth=1 https://github.com/dalibo/temboard/ /root/temboard ; \
    cd /root/temboard/ui ; \
    python setup.py bdist_wheel ; \
    :

FROM python:3.7-slim

RUN set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        sudo \
    ; \
    rm -rf /var/lib/apt/lists/* ; \
    apt-get clean ; \
    :

COPY --from=builder /root/temboard/ui/dist/*.whl /root
COPY entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it

RUN set -ex; \
    chmod 0755 /usr/local/bin/wait-for-it ; \
    pip --no-cache-dir install /root/temboard*.whl psycopg2-binary ; \
    useradd --home-dir /var/lib/temboard --create-home --system temboard ; \
    mkdir -p /etc/temboard ; \
    chown temboard. /etc/temboard; \
    :

VOLUME /var/lib/temboard
VOLUME /etc/temboard

WORKDIR /var/lib/temboard
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard"]

EXPOSE 8888
