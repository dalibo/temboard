apropos:  #: Show dev Makefile help.
	@echo
	@echo "    temBoard development"
	@echo
	@echo "make target available:"
	@echo
	@gawk 'match($$0, /([^:]*):.+#'': (.*)/, m) { printf "    %-16s%s\n", m[1], m[2]}' $(MAKEFILE_LIST) | sort
	@echo
	@echo "See docs/CONTRIBUTING.md for details."
	@echo

develop: develop-3.6  #: Create Pyton venv and docker services.

develop-%:
	$(MAKE) venv-$*
	$(MAKE) install-$*
	.venv-py$*/bin/pip install -r docs/requirements.txt
	docker-compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 psql -t -c 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	. .venv-py$*/bin/activate; PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 DEV=1 ui/share/create_repository.sh
	docker-compose up -d
	@echo
	@echo
	@echo "    You can now execute temBoard UI with .venv-py$*/bin/temboard"
	@echo
	@echo

venv-%:
	python$* -m venv .venv-py$*/

install-%:
	.venv-py$*/bin/pip install -r ui/requirements-dev.txt -e ui/

clean:  #: Trash venv and containers.
	docker-compose down --volumes --remove-orphans
	rm -rf .venv-py*

# This is the default compose project name as computed by docker-compose. See
# https://github.com/docker/compose/blob/13bacba2b9aecdf1f3d9a4aa9e01fbc1f9e293ce/compose/cli/command.py#L191
COMPOSE_PROJECT=$(notdir $(CURDIR))
# Spawning a networks for each agent is costly. Default docker installation
# supports a few dozens of networks limited by available IP. Reuse default
# network from docker-compose.yml run.
NETWORK=$(COMPOSE_PROJECT)_default

mass-agents:  #: Interactively trigger new agent.
	seq 2347 3000 | xargs --interactive -I% \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(NETWORK) \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		up -d

clean-agents:  #: Aggressively trash agent from mass-agents.
	seq 2347 3000 | xargs --verbose -I% --max-procs 4 \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(subst -,,$(notdir $(CURDIR)))_default \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		down --volumes

VERSION=$(shell cd ui; python setup.py --version)
BRANCH?=v$(firstword $(subst ., ,$(VERSION)))
GIT_REMOTE=git@github.com:dalibo/temboard.git
release:  #: Tag and push a new git release
	$(info Checking we are on branch $(BRANCH).)
	git rev-parse --abbrev-ref HEAD | grep -q '^$(BRANCH)$$'
	$(info Checking agent and UI version are same)
	grep -q "$(VERSION)" agent/temboardagent/version.py
	cd ui/; python setup.py egg_info
	cd agent/; python setup.py egg_info
	git commit ui/temboardui/version.py agent/temboardagent/version.py -m "Version $(VERSION)"
	$(info Checking source tree is clean)
	git diff --quiet
	git tag --annotate --message "Version $(VERSION)" $(VERSION)
	git push --follow-tags $(GIT_REMOTE) refs/heads/$(BRANCH):refs/heads/$(BRANCH)
