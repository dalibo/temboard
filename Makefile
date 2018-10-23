VERSION=$(shell python setup.py --version)

all:
	@echo Working on temboard $(VERSION)

release:
	python setup.py egg_info
	git commit setup.py -m "Version $(VERSION)"
	git tag $(VERSION)
	git push git@github.com:dalibo/temboard-agent.git
	git push --tags git@github.com:dalibo/temboard-agent.git

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python3 setup.py sdist bdist_wheel upload -r pypi

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard_CHANGEME.key -sha256 -days 1095 -out share/temboard_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard_ca_certs_CHANGEME.pem -CAkey share/temboard_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard_CHANGEME.pem
	rm -f request.pem share/temboard_ca_certs_CHANGEME.srl
