DISTDIR=../../dist
DPUT=labs

all: jessie stretch

jessie stretch:
	mkdir -p $(DISTDIR)
	docker-compose run --rm $@
	./mkchanges.sh $$(readlink -e $(DISTDIR)/last_build.deb) $@

push:
	version=$$(dpkg-deb -f ../../dist/last_build.deb  Version | grep -Po '.*(?=-1dlb.*)'); \
	find $(DISTDIR) -name "temboard_$${version}-1dlb*.changes" | xargs -rt dput $(DPUT)
