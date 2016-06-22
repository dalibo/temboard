#!/bin/bash

function clean_deb {
        rm -rf temboard-ui
        rm -f temboard-ui.debhelper.log
        rm -f temboard-ui.postinst.debhelper
        rm -f temboard-ui.postrm.debhelper
        rm -f temboard-ui.prerm.debhelper
        rm -f temboard-ui.substvars
        rm -rf ../build/
        rm -rf ../temboard-ui.egg-info/
}

clean_deb
cd ..
dpkg-buildpackage -b
cd debian/
clean_deb
