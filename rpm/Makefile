build:
	diff -Naur ../share/temboard-agent.conf temboard-agent.rpm.conf > temboard-agent.conf.patch; \
	cd ..; python setup.py sdist; \
	cp rpm/temboard-agent.conf.patch dist/.; \
	cp rpm/temboard-agent.service dist/.; \
	cp rpm/temboard-agent.init dist/.; \
	rpmbuild --define "_topdir `pwd`/rpm" --define "_sourcedir `pwd`/dist" -ba rpm/temboard-agent.spec;
