NAME="dalibo/temboard-agent"

build:
	docker build --build-arg http_proxy --tag $(NAME) .

clean:
	docker images --quiet $(NAME) | xargs --no-run-if-empty --verbose docker rmi -f

# Easy development of entrypoint.sh: make dev and docker-compose exec agent
# bash. Now edit entrypoint.sh and just call it as docker-entrypoint.sh inside
# the container to test it.
dev:
	docker-compose -f ../docker-compose.yml -f ./docker-compose.dev.yml up
