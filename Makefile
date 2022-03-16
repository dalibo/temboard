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

develop: develop-3.6  #: Create Python venv and docker services.
develop-2.7::  #: Create development environment for Python 2.7.
develop-%::
	$(MAKE) install-$*
	. .venv-py$*/bin/activate; $(MAKE) repository
	docker-compose up -d
	@echo
	@echo
	@echo "    You can now execute temBoard UI with .venv-py$*/bin/temboard"
	@echo
	@echo

repository:  #: Initialize temboard UI database.
	docker-compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 psql -t -c 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 DEV=1 ui/share/create_repository.sh

venv-%:
	PATH="$$(readlink -e $${PYENV_ROOT}/versions/$**/bin | sort -rV | head -1):$(PATH)" python$* -m venv .venv-py$*/
	.venv-py$*/bin/python --version  # pen test

venv-2.7:
	PATH="$$(readlink -e $${PYENV_ROOT}/versions/2.7*/bin | sort -rV | head -1):$(PATH)" python2.7 -m virtualenv .venv-py2.7/
	.venv-py2.7/bin/python --version  # pen test

install-%: venv-%
	.venv-py$*/bin/pip install -r docs/requirements.txt -r ui/requirements-dev.txt -e ui/
	.venv-py$*/bin/temboard --version  # pen test

clean:  #: Trash venv and containers.
	docker-compose down --volumes --remove-orphans
	rm -rf .venv-py* site/

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
