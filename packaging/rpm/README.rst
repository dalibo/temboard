=============================
 Packaging for RHEL / CentOS
=============================

The ``packaging/rpm`` directory contains rpm packaging of temBoard from released
tarball on PyPI or from a snapshot.


Building and uploading
----------------------

The ``all`` target builds packages for every supported distributions and put
them in upload directory. ``push`` target effectively upload RPMs to Dalibo Labs
YUM repository. Once you have setup your host for building, just run:

::

   make all push

The packages are stored in ``dist/rpm/`` at the root of the project.


Building a snapshot
-------------------

You can override the version to be built using ``VERSION`` env var. Ensure you
have the corresponding source tarball in ``dist/`` directory, otherwise, the
script will try to download the sources from PyPI.

::

   check-manifest
   python setup.py sdist
   VERSION=$(python setup.py --version) make -C packaging/rpm/ all push


Setup
-----

Package building requires Docker and Docker Compose for isolation. For
uploading, you need to have ``yum-labs`` project aside temboard clone.


Development
-----------

First, run docker container for interactive usage:

::

   docker-compose run --rm centos7 /bin/bash

If you get no output just after the run, type ``ENTER`` or ``CTRL+L`` to
redraw.

Top srcdir is mounted as ``/workspace/``. Just call
``/workspace/packaging/rpm/build.sh`` to build the RPM package.

Once you quit the shell, the container is destroyed.
