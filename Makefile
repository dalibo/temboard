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

DOCKER_MAX_VERSION=30
develop: develop-3.9  #: Create Python venv and docker services.
develop-%:: .env
	@dev/bin/checkdocker $(DOCKER_MAX_VERSION)
	git config blame.ignoreRevsFile dev/git-blame-ignore-revs
	if [ -d ~/.config/lnav/formats ] ; then ln -fsTv $$PWD/dev/lnav/formats ~/.config/lnav/formats/temboard ; fi
	$(MAKE) -j 2 install-$* ui/build/bin/prometheus ui/build/bin/promtool
	mkdir -p dev/temboard
	cd ui/; npm install-clean
	cd ui/; npm run build
	uv run $(MAKE) repository
	docker image remove --force dalibo/temboard-agent:dev
	docker compose build --pull agent0
	docker compose up -d
	@echo
	@echo
	@echo "    You can now execute temBoard UI with uv run temboard"
	@echo
	@echo

.env: dev/bin/mkenv
	$^ > $@

repository:  #: Initialize temBoard UI database.
	docker compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGDATABASE=postgres PGHOST=0.0.0.0 psql -Xtc 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	PGHOST=0.0.0.0 PGPASSWORD=postgres DEV=$${DEV-1} ui/share/create_repository.sh

recreate-repository:  #: Reinitialize temBoard UI database.
	docker compose up --detach --force-recreate --renew-anon-volumes repository
	$(MAKE) repository

restart-selenium:  #: Restart selenium development container.
	docker compose up --detach --force-recreate --renew-anon-volumes selenium

install-%:
	uv venv --clear --python=python$* --prompt="temboard-py$*"
	uv sync
	uv pip install --upgrade --no-deps --requirement agent/vendor.txt --target agent/temboardagent/_vendor
	uv pip install --upgrade --no-deps --requirement ui/vendor.txt --target ui/temboardui/_vendor
	uv run temboard --version  # smoke test
	uv run temboard-agent --version  # smoke test

# Vendoring

pip-locks: ui/vendor.txt agent/vendor.txt

# compile dependencies
%/vendor.txt: %/vendor.in
	uv pip compile --python-version=3.9 --upgrade $< -o $@

#LTS
PROMETHEUS_VERSION=2.53.0
dev/downloads/prometheus-%.linux-amd64.tar.gz:
	mkdir -p $(dir $@)
	curl --fail --silent -L "https://github.com/prometheus/prometheus/releases/download/v$*/$(notdir $@)" --output $@

ui/build/bin/prometheus ui/build/bin/promtool: dev/downloads/prometheus-$(PROMETHEUS_VERSION).linux-amd64.tar.gz
	mkdir -p $(dir $@)
	tar --extract --file "$<" --directory "$(dir $@)" --strip-component=1 --touch "prometheus-$(PROMETHEUS_VERSION).linux-amd64/$(notdir $@)"
	"$@" --version  # Smoketest

clean:  #: Trash venv and containers.
	docker compose down --volumes --remove-orphans
	docker rmi --force dalibo/temboard-agent:dev
	rm -rf .venv/ dev/venv-py* dev/build/ dev/prometheus/targets/temboard-dev.yaml
	rm -vf ui/build/bin/prometheus ui/build/bin/promtool
	rm -rf agent/build/ .env agent/.coverage
	rm -rf agent/temboardagent/_vendor ui/temboardui/_vendor
	rm -rvf ui/build/ ui/.coverage
	$(MAKE) clean-static

distclean: clean  #: Clean also dev env caches.
	rm -rvf dev/downloads/

# This is the default compose project name as computed by docker compose. See
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
		docker compose \
			--project-name temboardagent% \
			--file dev/docker-compose.massagent.yml \
		up -d

clean-agents:  #: Aggressively trash agent from mass-agents.
	seq 2348 3000 | xargs --verbose -I% --max-procs 4 \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(subst -,,$(notdir $(CURDIR)))_default \
		docker compose \
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
	ruff check
	ruff format --check
	pytest --exitfirst agent/tests/unit/
	pytest --exitfirst ui/tests/unit/
	pytest --exitfirst tests/

clean-tests:  #: Clean tests runtime files
	rm -rf tests/downloads/ tests/logs/ tests/screenshots/

prom-targets: dev/prometheus/targets/temboard-dev.yaml  #: Generate Prometheus dev targets.
dev/prometheus/targets/temboard-dev.yaml: dev/bin/mktargets .env
	$^ > $@

VERSION=$(shell uv --directory=ui/ version --short)
BRANCH?=master
# When stable branch v8 is created, use this:
# BRANCH?=v$(firstword $(subst ., ,$(VERSION)))

# To test release target, override GIT_REMOTE with your own fork.
REMOTE=git@github.com:dalibo/temboard.git
release:  #: Tag and push a new git release.
	@echo Checking we are on branch $(BRANCH).
	@git rev-parse --abbrev-ref HEAD | grep -q '^$(BRANCH)$$'
	@echo Checking $(BRANCH) branch is uptodate.
	@git fetch --quiet $(REMOTE) refs/heads/$(BRANCH)
	@git diff --check @..FETCH_HEAD
	@echo Checking agent and UI version are same.
	@grep -Fq "$(VERSION)" agent/pyproject.toml
	@echo Checking version is PEP440 compliant.
	@pep440deb "$(VERSION)" >/dev/null
	@echo Creating release commit.
	@git commit --only --quiet agent/pyproject.toml ui/pyproject.toml -m "Version $(VERSION)"
	@echo Checking source tree is clean.
	@git diff --quiet
	@echo Tagging v$(VERSION).
	@git tag --annotate --message "Version $(VERSION)" v$(VERSION)
	@echo Pushing tag to $(REMOTE).
	@git push --follow-tags $(REMOTE) refs/heads/$(BRANCH):refs/heads/$(BRANCH)
	@echo "Cleaning dist dirs."
	@rm -rf agent/dist/ ui/dist/

release-notes:  #: Extract changes for current release
	FINAL_VERSION="$(shell echo $(VERSION) | grep -Po '([^a-z]{3,})')" ; sed -En "/Unreleased/d;/^#+ $$FINAL_VERSION/,/^#/p" CHANGELOG.md  | sed '1d;$$d'

dist: dist-agent dist-ui  #: Build sources and wheels.
dist-ui:
	test -f ui/temboardui/static/dist/.vite/manifest.json
	uv build -o ui/dist/ ui/

dist-agent:
	uv build -o agent/dist/ agent/

static:  #: Build UI browser assets.
	cd ui/; npm run build

clean-static:  #: Clean UI browser assets.
	rm -vrf \
		ui/temboardui/static/dist

download-eggs:  #: Download Python eggs from PyPI
	pip3 download --no-deps --dest agent/dist/ temboard-agent==$(VERSION)
	pip3 download --no-deps --dest ui/dist/ temboard==$(VERSION)

YUM_LABS?=../yum-labs
CURL=curl --fail --create-dirs --location --silent --show-error
GH_DOWNLOAD=https://github.com/dalibo/temboard/releases/download/v$(VERSION)
AGENT_DIST_BASE=agent/dist/temboard-agent
UI_DIST_BASE=ui/dist/temboard
download-packages: download-rhel9 download-rhel8  download-deb-bookworm download-deb-bullseye download-deb-noble download-deb-jammy #: Download packages from GitHub release
download-rhel%:
	$(CURL) --output-dir agent/dist/ --remote-name $(GH_DOWNLOAD)/temboard-agent-$(VERSION)-1.el$*.noarch.rpm
	$(CURL) --output-dir ui/dist/ --remote-name $(GH_DOWNLOAD)/temboard-$(VERSION)-1.el$*.noarch.rpm

DEBIANVERSION=$(shell pep440deb $(VERSION))
# GitHub replace tilde by dot in asset filename.
GH_DEBIANVERSION=$(subst ~,.,$(DEBIANVERSION))
download-deb-%:
	$(CURL) --output $(AGENT_DIST_BASE)_$(DEBIANVERSION)-0dlb1$*1_all.deb -LO $(GH_DOWNLOAD)/temboard-agent_$(GH_DEBIANVERSION)-0dlb1$*1_all.deb
	$(CURL) --output $(UI_DIST_BASE)_$(DEBIANVERSION)-0dlb1$*1_amd64.deb -LO $(GH_DOWNLOAD)/temboard_$(GH_DEBIANVERSION)-0dlb1$*1_amd64.deb

publish-packages: publish-rhel publish-deb-bookworm publish-deb-bullseye publish-deb-noble publish-deb-jammy  #: Upload packages to Dalibo Labs repositories.
publish-rhel: copy-rhel9 copy-rhel8
	@if expr match "$(VERSION)" ".*[a-z]\+" >/dev/null; then echo 'Refusing to publish prerelease in YUM repository.'; false ; fi
	@make -C $(YUM_LABS) push createrepos clean

publish-deb-%:
	@if expr match "$(VERSION)" ".*[a-z]\+" >/dev/null; then echo 'Refusing to publish prerelease in APT repository.'; false ; fi
	agent/packaging/deb/mkchanges.sh agent/dist/temboard-agent_$(DEBIANVERSION)-0dlb1$*1_all.deb $*
	ui/packaging/deb/mkchanges.sh ui/dist/temboard_$(DEBIANVERSION)-0dlb1$*1_amd64.deb $*
	dput labs agent/dist/temboard-agent_$(DEBIANVERSION)-0dlb1$*1_all_$*.changes ui/dist/temboard_$(DEBIANVERSION)-0dlb1$*1_amd64_$*.changes

copy-rhel%:
	rm -rvf $(YUM_LABS)/rpms/RHEL$*-x86_64/*.rpm
	mkdir -p $(YUM_LABS)/rpms/RHEL$*-x86_64/
	cp -f agent/dist/temboard-agent-$(VERSION)-1.el$*.noarch.rpm ui/dist/temboard-$(VERSION)-1.el$*.noarch.rpm $(YUM_LABS)/rpms/RHEL$*-x86_64/

docker-build-agent:
	type pep440deb
	docker build \
		--progress=plain \
		--file agent/packaging/docker/Dockerfile \
		--build-arg http_proxy \
		--build-arg VERSION=$(DEBIANVERSION) \
		--tag dalibo/temboard-agent:snapshot \
		agent/

docker-build-ui:
	type pep440deb
	docker build \
		--progress=plain \
		--file ui/packaging/docker/Dockerfile \
		--build-arg http_proxy \
		--build-arg VERSION=$(DEBIANVERSION) \
		--tag dalibo/temboard:snapshot \
		ui/

# Disable pager for psql.
export PAGER=
