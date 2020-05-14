default:

run:
	docker-compose up --exit-code-from test --abort-on-container-exit test

run-all:
	$(MAKE) run
	TAG=centos7 POSTGRES_VERSION=11 $(MAKE) run
	TAG=centos7 POSTGRES_VERSION=10 $(MAKE) run
	TAG=centos7 POSTGRES_VERSION=9.6 $(MAKE) run
	TAG=centos6 POSTGRES_VERSION=9.5 $(MAKE) run

shell:
	docker-compose exec test /bin/bash

PYTEST_ARGS?=
pytest:
	TBD_WORKPATH="/tmp" sudo -Eu testuser pytest -vs -p no:cacheprovider $(PYTEST_ARGS)
