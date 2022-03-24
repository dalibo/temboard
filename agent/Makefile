$(info Reading current version)
VERSION=$(shell python setup.py --version)

all:
	@echo Working on temboard-agent $(VERSION)

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python -c 'import temboardagent.toolkit'
	python setup.py sdist bdist_wheel
	twine upload dist/temboard-agent-$(VERSION).tar.gz $$(ls dist/temboard_agent-$(VERSION)-*.whl)

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard-agent_CHANGEME.key -sha256 -days 1095 -out share/temboard-agent_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard-agent_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard-agent_ca_certs_CHANGEME.pem -CAkey share/temboard-agent_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard-agent_CHANGEME.pem
	rm -f request.pem share/temboard-agent_ca_certs_CHANGEME.srl
