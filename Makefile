default:

devenv:
	docker-compose up -d repository
	for i in $$(seq 10) ; do if PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 psql -t -c 'SELECT version();' "connect_timeout=15" ; then break ; else sleep 1 ; fi ; done
	PGPASSWORD=postgres PGUSER=postgres PGHOST=0.0.0.0 DEV=1 ui/share/create_repository.sh
	docker-compose up -d
	docker-compose exec agent0 /bin/bash -c 'pip install -e /usr/local/src/temboard/agent/ psycopg2-binary hupper'
	docker-compose exec agent1 /bin/bash -c 'pip install -e /usr/local/src/temboard/agent/ psycopg2-binary hupper'

# This is the default compose project name as computed by docker-compose. See
# https://github.com/docker/compose/blob/13bacba2b9aecdf1f3d9a4aa9e01fbc1f9e293ce/compose/cli/command.py#L191
COMPOSE_PROJECT=$(notdir $(CURDIR))
# Spawning a networks for each agent is costly. Default docker installation
# supports a few dozens of networks limited by available IP. Reuse default
# network from docker-compose.yml run.
NETWORK=$(COMPOSE_PROJECT)_default

mass-agents:
	seq 2347 3000 | xargs --interactive -I% \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(NETWORK) \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		up -d

clean-agents:
	seq 2347 3000 | xargs --verbose -I% --max-procs 4 \
		env \
			TEMBOARD_REGISTER_PORT=% \
			NETWORK=$(subst -,,$(notdir $(CURDIR)))_default \
		docker-compose \
			--project-name temboardagent% \
			--file docker/docker-compose.agent.yml \
		down --volumes
