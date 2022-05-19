DISTDIR=$(wildcard ../..)/dist
YUM_LABS?=$(wildcard ../../../yum-labs)

release:
	@make -sC $(YUM_LABS) clean
	$(MAKE) release-rhel8 release-rhel7

# Helper target to build and push altogether.
release-rhel%:
	$(MAKE) build-rhel$*
	mkdir -p $(YUM_LABS)/rpms/RHEL$*-x86_64
	cp -fl $$(readlink -e $(DISTDIR)/temboard-last.rpm) $(YUM_LABS)/rpms/RHEL$*-x86_64/
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
