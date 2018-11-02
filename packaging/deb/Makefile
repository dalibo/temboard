all:

build: deb

deb:
	mkdir -p ../dist/
	docker-compose run --rm debian
	$(MAKE) changes-wheezy
	$(MAKE) changes-jessie
	$(MAKE) changes-stretch

changes-%:
	./mkchanges.sh $(shell readlink -e ../../dist/last_build.deb) $*

push:
	find ../../dist/ -name "temboard-agent_*-0dlb*.changes" | xargs -rt dput dalibo
