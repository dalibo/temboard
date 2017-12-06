default:

build:
	docker build -t dalibo/temboard-agent-func:centos6 -f Dockerfile.centos6 .
	docker build -t dalibo/temboard-agent-func:centos7 -f Dockerfile.centos7 .

run:
	docker-compose up
	if docker-compose ps | grep 'Exit [1-9]' ; then exit 1; fi
