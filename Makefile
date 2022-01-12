VERSION=$(shell python setup.py --version)
BRANCH?=v$(firstword $(subst ., ,$(VERSION)))
GIT_REMOTE=git@github.com:dalibo/temboard.git

all:
	@echo Working on temboard $(VERSION)

release:
	@echo Checking we are on branch $(BRANCH).
	git rev-parse --abbrev-ref HEAD | grep -q '^$(BRANCH)$$'
	python setup.py egg_info
	git commit temboardui/version.py -m "Version $(VERSION)"
	git tag --annotate --message "Version $(VERSION)" $(VERSION)
	git push --follow-tags $(GIT_REMOTE) refs/heads/$(BRANCH):refs/heads/$(BRANCH)

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python2 -c 'import temboardui.toolkit'
	@echo Clean build and dist directory
	rm -rf build
	check-manifest
	python2.7 setup.py sdist bdist_wheel
	twine upload dist/temboard-$(VERSION).tar.gz dist/temboard-$(VERSION)-py2-none-any.whl

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard_CHANGEME.key -sha256 -days 1095 -out share/temboard_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard_ca_certs_CHANGEME.pem -CAkey share/temboard_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard_CHANGEME.pem
	rm -f request.pem share/temboard_ca_certs_CHANGEME.srl

devenv:
	docker-compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 psql -t -c 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 DEV=1 share/create_repository.sh
	docker-compose up -d

# This is the default compose project name as computed by docker-compose. See
# https://github.com/docker/compose/blob/13bacba2b9aecdf1f3d9a4aa9e01fbc1f9e293ce/compose/cli/command.py#L191
COMPOSE_PROJECT=$(notdir $(CURDIR))
# Spawning a networks for each agent is costly. Default docker installation
# supports a few dozens of networks limited by available IP. Reuse default
# network from docker-compose.yml run.
NETWORK=$(COMPOSE_PROJECT)_default

mass-agents:
	seq 2346 3000 | xargs --interactive -I% \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(NETWORK) \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		up -d

clean-agents:
	seq 2346 3000 | xargs --verbose -I% --max-procs 4 \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(subst -,,$(notdir $(CURDIR)))_default \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		down --volumes

.PHONY: docs docs-serve
docs: site

docs-serve:
	mkdocs serve

site: docs/* mkdocs.yml
	mkdocs build --theme readthedocs
