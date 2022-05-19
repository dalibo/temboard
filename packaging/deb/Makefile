DISTDIR=../../dist
DPUT=labs

release:
	$(MAKE) build-bullseye build-buster build-stretch
	$(MAKE) push

build-%:
	mkdir -p $(DISTDIR)
	docker-compose run --rm $*
	./mkchanges.sh $$(readlink -e $(DISTDIR)/temboard_last.deb) $*

push:
	version=$$(dpkg-deb -f ../../dist/temboard_last.deb  Version | grep -Po '.*(?=-0dlb.*)'); \
	find $(DISTDIR) -name "temboard_$${version}-0dlb*.changes" | xargs -rt dput $(DPUT)
