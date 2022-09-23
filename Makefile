apropos:  #: Show dev Makefile help.
	@echo
	@echo "    temBoard development"
	@echo
	@echo "make target available:"
	@echo
	@gawk 'match($$0, /([^:]*):.+#'': (.*)/, m) { printf "    %-24s%s\n", m[1], m[2]}' $(MAKEFILE_LIST) | sort
	@echo
	@echo "See docs/CONTRIBUTING.md for details."
	@echo

develop: develop-3.6  #: Create Python venv and docker services.
develop-2.7:: .env  #: Create development environment for Python 2.7.
develop-%:: .env
	$(MAKE) install-$*
	cd ui/; npm install-clean
	cd ui/; npm run build
	. dev/venv-py$*/bin/activate; $(MAKE) repository
	docker-compose build
	docker-compose up -d
	@echo
	@echo
	@echo "    You can now execute temBoard UI with dev/venv-py$*/bin/temboard"
	@echo
	@echo

.env: dev/mkenv
	$^ > $@

repository:  #: Initialize temBoard UI database.
	docker-compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 psql -t -c 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	PGHOST=0.0.0.0 PGPASSWORD=postgres DEV=$${DEV-1} ui/share/create_repository.sh

recreate-repository:  #: Reinitialize temBoard UI database.
	docker-compose up --detach --force-recreate --renew-anon-volumes repository
	$(MAKE) repository

restart-selenium:  #: Restart selenium development container.
	docker-compose up --detach --force-recreate --renew-anon-volumes selenium

venv-%:
	PATH="$$(readlink -e $${PYENV_ROOT}/versions/$**/bin | sort -rV | head -1):$(PATH)" python$* -m venv dev/venv-py$*/ --prompt "$${PWD##*/}-py$*"
	dev/venv-py$*/bin/pip install -U pip   # Upgrade pip to install cryptography
	dev/venv-py$*/bin/python --version  # pen test
	dev/venv-py$*/bin/pip --version  # pen test

venv-2.7:
	PATH="$$(readlink -e $${PYENV_ROOT}/versions/2.7*/bin | sort -rV | head -1):$(PATH)" python2.7 -m virtualenv dev/venv-py2.7/ --prompt "$${PWD##*/}-py2.7"
	dev/venv-py2.7/bin/python --version  # pen test

install-%: venv-%
	dev/venv-py$*/bin/pip install -r docs/requirements.txt -r dev/requirements.txt -e agent/ -e ui/
	dev/venv-py$*/bin/temboard --version  # pen test
	dev/venv-py$*/bin/temboard-agent --version  # pen test

install-2.7: venv-2.7
	dev/venv-py2.7/bin/pip install -r docs/requirements.txt -r dev/requirements.txt -e ui/
	dev/venv-py2.7/bin/temboard --version  # pen test

clean:  #: Trash venv and containers.
	docker-compose down --volumes --remove-orphans
	docker rmi --force dalibo/temboard-agent:dev
	rm -rf dev/venv-py* .venv-py* dev/build/ dev/prometheus/targets/temboard-dev.yaml
	rm -rf agent/build/ .env agent/.coverage
	rm -rvf ui/build/ ui/.coverage
	$(MAKE) clean-static

# This is the default compose project name as computed by docker-compose. See
# https://github.com/docker/compose/blob/13bacba2b9aecdf1f3d9a4aa9e01fbc1f9e293ce/compose/cli/command.py#L191
COMPOSE_PROJECT=$(notdir $(CURDIR))
# Spawning a networks for each agent is costly. Default docker installation
# supports a few dozens of networks limited by available IP. Reuse default
# network from docker-compose.yml run.
NETWORK=$(COMPOSE_PROJECT)_default

mass-agents:  #: Interactively trigger new agent.
	seq 2348 3000 | xargs --interactive -I% \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(NETWORK) \
		docker-compose \
			--project-name temboardagent% \
			--file dev/docker-compose.massagent.yml \
		up -d

clean-agents:  #: Aggressively trash agent from mass-agents.
	seq 2348 3000 | xargs --verbose -I% --max-procs 4 \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(subst -,,$(notdir $(CURDIR)))_default \
		docker-compose \
			--project-name temboardagent% \
			--file dev/docker-compose.massagent.yml \
		down --volumes

renew-sslca:  #: Renew CA for self signed certificates.
	openssl req -batch -x509 -new -nodes -key agent/share/temboard-agent_CHANGEME.key -sha256 -days 1095 -out agent/share/temboard-agent_ca_certs_CHANGEME.pem
	openssl req -batch -x509 -new -nodes -key ui/share/temboard_CHANGEME.key -sha256 -days 1095 -out ui/share/temboard_ca_certs_CHANGEME.pem

renew-sslcert:  #: Renew self-signed SSL certificates.
	openssl req -batch -new -key agent/share/temboard-agent_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA agent/share/temboard-agent_ca_certs_CHANGEME.pem -CAkey agent/share/temboard-agent_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out agent/share/temboard-agent_CHANGEME.pem
	openssl req -batch -new -key ui/share/temboard_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA ui/share/temboard_ca_certs_CHANGEME.pem -CAkey ui/share/temboard_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out ui/share/temboard_CHANGEME.pem
	rm -f request.pem agent/share/temboard-agent_ca_certs_CHANGEME.srl ui/share/temboard_ca_certs_CHANGEME.srl

.PHONY: tests
tests:  #: Execute all tests.
	cd agent/; flake8
	cd ui/; flake8
	flake8 tests/ dev/importlog.py
	pytest -x agent/tests/unit/
	pytest -x ui/tests/unit/
	pytest -x tests/

clean-tests:  #: Clean tests runtime files
	rm -rf tests/downloads/ tests/logs/ tests/screenshots/

prom-targets: dev/prometheus/targets/temboard-dev.yaml  #: Generate Prometheus dev targets.
dev/prometheus/targets/temboard-dev.yaml: dev/prometheus/mktargets .env
	$^ > $@

VERSION=$(shell cd ui; python setup.py --version)
BRANCH?=master
# When stable branch v8 is created, use this:
# BRANCH?=v$(firstword $(subst ., ,$(VERSION)))

# To test release target, override GIT_REMOTE with your own fork.
GIT_REMOTE=git@github.com:dalibo/temboard.git
release:  #: Tag and push a new git release.
	$(info Checking we are on branch $(BRANCH).)
	git rev-parse --abbrev-ref HEAD | grep -q '^$(BRANCH)$$'
	$(info Checking agent and UI version are same)
	grep -q "$(VERSION)" agent/temboardagent/version.py
	git commit agent/temboardagent/version.py ui/temboardui/version.py -m "Version $(VERSION)"
	$(info Checking source tree is clean)
	git diff --quiet
	git tag --annotate --message "Version $(VERSION)" v$(VERSION)
	git push --follow-tags $(GIT_REMOTE) refs/heads/$(BRANCH):refs/heads/$(BRANCH)

dist:  #: Build sources and wheels.
	cd agent/; python3 setup.py sdist bdist_wheel
	test -f ui/temboardui/static/manifest.json
	cd ui/; python3 setup.py sdist bdist_wheel --universal

static:  #: Build UI browser assets.
	cd ui/; npm run build

clean-static:  #: Clean UI browser assets.
	rm -vrf \
		ui/temboardui/static/*.* \
		ui/temboardui/static/css/ \
		ui/temboardui/static/images/ \
		ui/temboardui/static/js/

download-eggs:  #: Download Python eggs from PyPI
	pip3 download --no-deps --dest agent/dist/ temboard-agent==$(VERSION)
	pip3 download --no-deps --dest ui/dist/ temboard==$(VERSION)

YUM_LABS?=../yum-labs
CURL=curl --fail --create-dirs --location --silent --show-error
GH_DOWNLOAD=https://github.com/dalibo/temboard/releases/download/v$(VERSION)
AGENT_DIST_BASE=agent/dist/temboard-agent
UI_DIST_BASE=agent/dist/temboard
download-packages: download-rhel9 download-rhel8 download-rhel7 download-deb-bullseye download-deb-buster download-deb-stretch  #: Download packages from GitHub release
download-rhel%:
	$(CURL) --output-dir agent/dist/ --remote-name $(GH_DOWNLOAD)/temboard-agent-$(VERSION)-1.el$*.noarch.rpm
	$(CURL) --output-dir ui/dist/ --remote-name $(GH_DOWNLOAD)/temboard-$(VERSION)-1.el$*.noarch.rpm

DEBIANVERSION=$(shell pep440deb $(VERSION))
# GitHub replace tilde by dot in asset filename.
GH_DEBIANVERSION=$(subst ~,.,$(DEBIANVERSION))
download-deb-%:
	$(CURL) --output $(AGENT_DIST_BASE)_$(DEBIANVERSION)-0dlb1$*1_all.deb -LO $(GH_DOWNLOAD)/temboard-agent_$(GH_DEBIANVERSION)-0dlb1$*1_all.deb
	$(CURL) --output $(UI_DIST_BASE)_$(DEBIANVERSION)-0dlb1$*1_amd64.deb -LO $(GH_DOWNLOAD)/temboard_$(GH_DEBIANVERSION)-0dlb1$*1_amd64.deb

publish-packages: publish-rhel publish-deb-bullseye publish-deb-buster publish-deb-stretch  #: Upload packages to Dalibo Labs repositories.
publish-rhel: copy-rhel9 copy-rhel8 copy-rhel7
	@make -C $(YUM_LABS) push createrepos clean

publish-deb-%:
	agent/packaging/deb/mkchanges.sh agent/dist/temboard-agent_$(DEBIANVERSION)-0dlb1$*1_all.deb $*
	ui/packaging/deb/mkchanges.sh ui/dist/temboard_$(DEBIANVERSION)-0dlb1$*1_amd64.deb $*
	dput labs agent/dist/temboard-agent_$(DEBIANVERSION)-0dlb1$*1_all_$*.changes ui/dist/temboard_$(DEBIANVERSION)-0dlb1$*1_amd64_$*.changes

copy-rhel%:
	rm -rvf $(YUM_LABS)/rpms/RHEL$*-x86_64/*.rpm
	mkdir -p $(YUM_LABS)/rpms/RHEL$*-x86_64/
	cp -f agent/dist/temboard-agent-$(VERSION)-1.el$*.noarch.rpm ui/dist/temboard-$(VERSION)-1.el$*.noarch.rpm $(YUM_LABS)/rpms/RHEL$*-x86_64/

DOCKER_TAG=$(VERSION)
docker-build-agent:
	docker build \
		--file agent/packaging/docker/Dockerfile \
		--build-arg http_proxy \
		--build-arg VERSION=$(DEBIANVERSION) \
		--tag dalibo/temboard-agent:$(DOCKER_TAG) \
		--tag dalibo/temboard-agent:8 \
		--tag dalibo/temboard-agent:latest \
		agent/
