all: bullseye buster stretch

bullseye buster stretch:
	$(MAKE) build-$@
	$(MAKE) push

build-%:
	mkdir -p ../../dist/
	docker-compose run --rm $*
	./mkchanges.sh $(shell readlink -e ../../dist/temboard-agent_last.deb) $*

push:
	version=$$(dpkg-deb -f ../../dist/temboard-agent_last.deb  Version | grep -Po '.*(?=-0dlb.*)'); \
	find ../../dist/ -name "temboard-agent_$${version}-0dlb*.changes" | xargs -rt dput labs
