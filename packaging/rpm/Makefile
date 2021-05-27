DISTDIR=$(wildcard ../..)/dist
YUM_LABS?=$(wildcard ../../../yum-labs)

all:
	@make -sC $(YUM_LABS) clean
	$(MAKE) build-centos8 build-centos7

# Helper target to build and push altogether.
centos8 centos7:
	$(MAKE) build-$@
	$(MAKE) push

# Build RPM for either centos7 or centos8
build-centos%:
	if rpm --eval centos%dist 2>/dev/null | grep -q centos$*; then \
		./build.sh; \
	else \
		docker-compose run --rm centos$*; \
	fi
	mkdir -p $(YUM_LABS)/rpms/CentOS$*-x86_64
	cp -fl $$(readlink -e $(DISTDIR)/temboard-agent-last.rpm) $(YUM_LABS)/rpms/CentOS$*-x86_64/

push:
	@make -C $(YUM_LABS) push createrepos clean

clean:
	rm -rf $(TOPDIR)
