DISTDIR=../../dist
DPUT=labs

all: jessie stretch

jessie stretch:
	mkdir -p $(DISTDIR)
	CODENAME=$@ docker-compose run --rm debian
	./mkchanges.sh $(shell readlink -e $(DISTDIR)/last_build_$@.deb) $@

push:
	version=$$(dpkg-deb -f ../../dist/last_build.deb  Version | grep -Po '.*(?=-0dlb.*)'); \
	find $(DISTDIR) -name "temboard_$${version}-0dlb*.changes" | xargs -rt dput $(DPUT)
