all:

build: deb-jessie deb-stretch

deb-%:
	CODENAME=$* docker-compose run --rm debian
	$(MAKE) changes-$*

changes-%:
	./mkchanges.sh $(shell readlink -e ../dist/last_build_$*.deb) $*

push:
	find ../dist/ -name "*.changes" | xargs -rlt dput dalibo
