-----------------------------
 Packaging for RHEL / CentOS
-----------------------------

The ``packaging/rpm`` directory contains RPM packaging of temBoard agent from
released tarball on PyPI or from a snapshot.


Requirements
------------

Package building requires Docker and Docker Compose for isolation. For
uploading, you need to have ``yum-labs`` project aside temboard-agent clone.
Override yum-labs directory using ``YUM_LABS`` environment variable.


Building and uploading
----------------------

The ``all`` target builds packages for every supported distributions and put
them in upload directory. ``push`` target effectively upload RPMs to Dalibo Labs
YUM repository. Once you have setup your host for building, just run:

The script builds the temboard agent version as defined in ``setup.py``. If the
source tarball does not exists in ``dist/``, the script fetches it from PyPI. You
can override the version built with ``VERSION`` environment variable.

::

    $ make all push

The packages are stored in ``dist/`` at the root of the project.


Building a snapshot
-------------------

Just create the tarball with ``setup.py sdist``.

::

    $ python setup.py sdist
    $ make -C packaging/rpm/ all


Development
-----------

The RPM spec file supports building a package for RHEL / CentOS version 7
and 8. To do so, it uses tests on the version, provided by the %{rhel} macro.

First, run docker container for interactive usage:

::

    $ docker-compose run --rm centos7 /bin/bash

If you get no output just after the run, type ``ENTER`` or ``CTRL+L`` to redraw.

Top source directory is mounted as ``/workspace/``. Just call
``/workspace/packaging/rpm/build.sh`` to build the RPM package.

Once you quit the shell, the container is destroyed.
