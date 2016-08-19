#!/bin/bash

function clean_deb {
        rm -rf temboard
        rm -f temboard.debhelper.log
        rm -f temboard.postinst.debhelper
        rm -f temboard.postrm.debhelper
        rm -f temboard.prerm.debhelper
        rm -f temboard.substvars
        rm -rf ../build/
        rm -rf ../temboard.egg-info/
}

clean_deb
cd ..
dpkg-buildpackage -b
cd debian/
clean_deb
