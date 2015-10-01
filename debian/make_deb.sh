#!/bin/bash

function clean_deb {
        rm -rf ganesh
        rm -f ganesh.debhelper.log
        rm -f ganesh.postinst.debhelper
        rm -f ganesh.postrm.debhelper
        rm -f ganesh.prerm.debhelper
        rm -f ganesh.substvars
        rm -rf ../build/
        rm -rf ../ganesh.egg-info/
}

clean_deb
cd ..
dpkg-buildpackage -b
cd debian/
clean_deb
