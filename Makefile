VERSION=$(shell python2 setup.py --version)

all:
	@echo Working on temboard-agent $(VERSION)

release:
	python2 setup.py egg_info
	git commit setup.py -m "Version $(VERSION)"
	git tag $(VERSION)
	git push git@github.com:dalibo/temboard-agent.git
	git push --tags git@github.com:dalibo/temboard-agent.git

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python2 setup.py sdist bdist_wheel upload -r pypi

shell:
	docker-compose exec agent bash

renew_ssl:
# Renew CA cert
	openssl req -batch -x509 -new -nodes -key share/temboard-agent_CHANGEME.key -sha256 -days 1095 -out share/temboard-agent_ca_certs_CHANGEME.pem
# Create a cert signing request
	openssl req -batch -new -key share/temboard-agent_CHANGEME.key -out request.pem
# Create the self signed certificate and clean request
	openssl x509 -req -in request.pem -CA share/temboard-agent_ca_certs_CHANGEME.pem -CAkey share/temboard-agent_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard-agent_CHANGEME.pem
	rm -f request.pem share/temboard-agent_ca_certs_CHANGEME.srl
