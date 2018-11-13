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
	python2.7 setup.py sdist bdist_wheel
	twine upload dist/temboard-$(VERSION).tar.gz dist/temboard-$(VERSION)-py2-none-any.whl
