default:

run:
	docker-compose up --exit-code-from test --abort-on-container-exit test

run-all:
	@# Please keep this matrix sync with .circleci/config.yml
	TAG=buster PYTHON=python3 TBD_PGVERSION=13 $(MAKE) run
	TAG=centos8 TBD_PGVERSION=12 $(MAKE) run
	TAG=centos7 TBD_PGVERSION=12 $(MAKE) run
	TAG=buster TBD_PGVERSION=11 $(MAKE) run
	TAG=stretch TBD_PGVERSION=10 $(MAKE) run
	TAG=centos8 TBD_PGVERSION=9.6 $(MAKE) run
	TAG=centos7 TBD_PGVERSION=9.6 $(MAKE) run

shell:
	docker-compose exec test /bin/bash
