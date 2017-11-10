VERSION=$(shell python setup.py --version)

all:
	@echo Working on temboard-agent $(VERSION)

release:
	python setup.py egg_info
	git commit setup.py -m "Version $(VERSION)"
	git tag $(VERSION)
	@echo
	@echo Now push with
	@echo
	@echo "    git push rw"
	@echo "    git push --tags rw"
	@echo
	@echo and upload with make upload

upload:
	@echo Checking we are on a tag
	git describe --exact-match --tags
	python3 setup.py sdist bdist_wheel upload -r pypi
