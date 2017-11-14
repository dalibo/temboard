build:
	diff -Naur ../share/temboard.conf temboard.rpm.conf > temboard.conf.patch; \
	cd ..; python setup.py sdist; \
	cp rpm/temboard.conf.patch dist/.; \
	cp rpm/temboardui.plugins.monitoring.model.orm.py.patch dist/.; \
	cp rpm/temboard.service dist/.; \
	cp rpm/temboard.init dist/.; \
	rpmbuild --define "_topdir `pwd`/rpm" --define "_sourcedir `pwd`/dist" -ba rpm/temboard.spec;
