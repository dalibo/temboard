FROM debian:bullseye-slim AS copier
# RUN --mount syntax does not accept arg. Thus first stage copy with arg in
# static path for future RUN --mount.
ARG VERSION
COPY dist/temboard-agent_${VERSION}-0dlb1bullseye1_all.deb /tmp/temboard-agent.deb

FROM debian:bullseye-slim

ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN set -ex; \
    chmod 0755 /usr/local/bin/wait-for-it; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends \
        openssl \
        postgresql-client \
        ssl-cert \
        sudo \
    ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*.7*; \
    :

ADD packaging/docker/sudoers /etc/sudoers.d/temboard-agent
ADD packaging/docker/entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN --mount=type=bind,from=copier,source=/tmp/temboard-agent.deb,target=/tmp/temboard-agent.deb \
    set -ex; \
    apt-get update -y ; \
    mkdir -p /usr/share/man/man1 /usr/share/man/man7 ; \
    apt-get install -y --no-install-recommends /tmp/temboard-agent.deb ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/* /usr/share/man/man*/*.7*; \
    temboard-agent --version ; \
    :

VOLUME /etc/temboard-agent
VOLUME /var/lib/temboard-agent
WORKDIR /var/lib/temboard-agent
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["temboard-agent"]
