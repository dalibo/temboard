DISTDIR=$(wildcard ../..)/dist
YUM_LABS?=$(wildcard ../../../yum-labs)

all:
	@make -sC $(YUM_LABS) clean
	$(MAKE) build-rhel8 build-rhel7

# Helper target to build and push altogether.
rhel8 rhel7:
	$(MAKE) build-$@
	mkdir -p $(YUM_LABS)/rpms/$(shell echo '$*' | tr '[:lower:]' '[:upper:]')-x86_64
	cp -fl $$(readlink -e $(DISTDIR)/temboard-last.rpm) $(YUM_LABS)/rpms/$(shell echo '$*' | tr '[:lower:]' '[:upper:]')-x86_64/
	$(MAKE) push

# Build RPM for either RHEL 7 or 8
build-rhel%:
	if rpm --eval rhel%dist 2>/dev/null | grep -q rhel$*; then \
		./build.sh; \
	else \
		docker-compose run --rm rhel$*; \
	fi

push:
	@make -C $(YUM_LABS) push createrepos clean

clean:
	rm -rf $(TOPDIR)
