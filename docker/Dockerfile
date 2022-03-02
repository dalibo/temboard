FROM python:3.6-slim AS builder

RUN apt-get update -y \
    && mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get install -y --no-install-recommends \
        git-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    ;

RUN set -ex; \
    git clone --depth=1 --recursive https://github.com/dalibo/temboard-agent /root/temboard-agent; \
    cd /root/temboard-agent ; \
    python setup.py bdist_wheel ; \
    :

FROM python:3.6-slim

COPY --from=builder /root/temboard-agent/dist/temboard*.whl /root/

RUN apt-get update -y \
    && mkdir -p /usr/share/man/man1 /usr/share/man/man7 \
    && apt-get install -y --no-install-recommends \
        docker.io \
        libltdl7 \
        postgresql-client \
        sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    ;

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN set -ex; \
    chmod 0755 /usr/local/bin/wait-for-it; \
    pip --no-cache-dir install /root/temboard*.whl psycopg2-binary; \
    :

VOLUME /etc/temboard-agent
VOLUME /var/lib/temboard-agent
WORKDIR /var/lib/temboard-agent
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard-agent"]

ADD sudoers /etc/sudoers.d/temboard-agent
ADD entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ADD pg_ctl_temboard.sh /usr/local/bin/pg_ctl_temboard.sh
