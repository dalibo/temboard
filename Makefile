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
