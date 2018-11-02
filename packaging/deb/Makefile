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

reprepro:
	test -f ./reprepro-config/reprepro-authorized_keys || cat ~/.ssh/*.pub > ./reprepro-config/reprepro-authorized_keys
	$(MAKE) reprepro-up

reprepro-%:
	docker-compose -f docker-compose.reprepro.yml $*

reprepro-trash:
	docker-compose -f docker-compose.reprepro.yml down -v
