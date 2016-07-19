#!/bin/bash

function clean_deb {
	rm -rf temboard-agent
	rm -f temboard-agent.debhelper.log
	rm -f temboard-agent.postinst.debhelper
	rm -f temboard-agent.postrm.debhelper
	rm -f temboard-agent.prerm.debhelper
	rm -f temboard-agent.substvars
	rm -rf ../build/
	rm -rf ../temboard-agent.egg-info/
}

clean_deb
cd ..
dpkg-buildpackage -b
cd debian/
clean_deb
