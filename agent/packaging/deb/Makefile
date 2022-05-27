DISTDIR=../../dist
DPUT=labs

default:

build-%:
	mkdir -p $(DISTDIR)
	docker-compose run --rm $*
	./mkchanges.sh $$(readlink -e $(DISTDIR)/temboard-agent_last.deb) $*

push:
	version=$$(dpkg-deb -f ../../dist/temboard-agent_last.deb  Version | grep -Po '.*(?=-0dlb.*)'); \
	find ../../dist/ -name "temboard-agent_$${version}-0dlb*.changes" | xargs -rt dput labs

release-%:
	$(MAKE) build-$@
	$(MAKE) push
