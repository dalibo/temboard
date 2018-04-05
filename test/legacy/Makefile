default:

run:
	docker-compose up --exit-code-from test --abort-on-container-exit test

shell:
	docker-compose exec test /bin/bash

PYTEST_ARGS?=
pytest:
	TBD_WORKPATH="/tmp" sudo -Eu testuser pytest -vs -p no:cacheprovider ./ $(PYTEST_ARGS)
