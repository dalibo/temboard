DISTDIR=$(wildcard ../..)/dist
YUM_LABS?=$(wildcard ../../../yum-labs)

all:
	@make -sC $(YUM_LABS) clean
	$(MAKE) build-rhel8 build-rhel7

# Helper target to build and push altogether.
rhel8 rhel7:
	$(MAKE) build-$@
	$(MAKE) push

# Build RPM for either rhel7 or rhel8
build-rhel%:
	if rpm --eval rhel%dist 2>/dev/null | grep -q rhel$*; then \
		./build.sh; \
	else \
		docker-compose run --rm rhel$*; \
	fi
	mkdir -p $(YUM_LABS)/rpms/RHEL$*-x86_64
	cp -fl $$(readlink -e $(DISTDIR)/temboard-agent-last.rpm) $(YUM_LABS)/rpms/RHEL$*-x86_64/

push:
	@make -C $(YUM_LABS) push createrepos clean

clean:
	rm -rf $(TOPDIR)
