DISTDIR=$(wildcard ../..)/dist
YUM_LABS?=$(wildcard ../../../yum-labs)

default:

build-rhel%:
	if rpm --eval rhel%dist 2>/dev/null | grep -q rhel$*; then \
		./build.sh; \
	else \
		docker-compose run --rm rhel$*; \
	fi

push:
	@make -C $(YUM_LABS) push createrepos clean

release-rhel%:
	make -sC $(YUM_LABS) clean
	$(MAKE) build-rhel$*
	mkdir -p $(YUM_LABS)/rpms/RHEL$*-x86_64
	cp -fl $$(readlink -e $(DISTDIR)/temboard-agent-last.rpm) $(YUM_LABS)/rpms/RHEL$*-x86_64/
	$(MAKE) push
