default:

build:
	docker build -t dalibo/temboard-agent-func .

run:
	docker-compose up
	if docker-compose ps | grep 'Exit [1-9]' ; then exit 1; fi
