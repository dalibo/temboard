VERSION=$(shell python setup.py --version)
BRANCH?=v$(firstword $(subst ., ,$(VERSION)))
GIT_REMOTE=git@github.com:dalibo/temboard.git

all:
	@echo Working on temboard $(VERSION)

release:
	@echo Checking we are on branch $(BRANCH).
	git rev-parse --abbrev-ref HEAD | grep -q '^$(BRANCH)$$'
	python setup.py egg_info
	git commit temboardui/version.py -m "Version $(VERSION)"
	git tag --annotate --message "Version $(VERSION)" $(VERSION)
	git push --follow-tags $(GIT_REMOTE) refs/heads/$(BRANCH):refs/heads/$(BRANCH)

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python -c 'import temboardui.toolkit'
	@echo Clean build and dist directory
	rm -rf build
	check-manifest
	python setup.py sdist bdist_wheel --universal
	twine upload dist/temboard-$(VERSION).tar.gz dist/temboard-$(VERSION)-py2.py3-none-any.whl

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard_CHANGEME.key -sha256 -days 1095 -out share/temboard_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard_ca_certs_CHANGEME.pem -CAkey share/temboard_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard_CHANGEME.pem
	rm -f request.pem share/temboard_ca_certs_CHANGEME.srl
