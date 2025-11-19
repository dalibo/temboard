FROM debian:bookworm-slim AS copier
# RUN --mount syntax does not accept arg. Thus first stage copy with arg in
# static path for future RUN --mount.
ARG VERSION
COPY dist/temboard_${VERSION}-0dlb1bookworm1_amd64.deb /tmp/temboard.deb

FROM debian:bookworm-slim

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN set -ex; \
    chmod 0755 /usr/local/bin/wait-for-it; \
    :

RUN set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        openssl \
        postgresql-client \
        ssl-cert \
        sudo \
    ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*; \
    :

ADD packaging/docker/entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ARG VERSION
RUN --mount=type=bind,from=copier,source=/tmp/temboard.deb,target=/tmp/temboard.deb \
    set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends /tmp/temboard.deb ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*; \
    temboard --version ; \
    :

VOLUME /var/lib/temboard
VOLUME /etc/temboard

WORKDIR /var/lib/temboard
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard"]

EXPOSE 8888
