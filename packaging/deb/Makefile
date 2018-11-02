all:

build: stretch jessie wheezy

stretch jessie wheezy:
	mkdir -p ../dist/
	docker-compose run --rm $@
	$(MAKE) changes-$@

changes-%:
	./mkchanges.sh $(shell readlink -e ../../dist/last_build.deb) $*

push:
	find ../../dist/ -name "temboard-agent_*-0dlb*.changes" | xargs -rt dput dalibo
