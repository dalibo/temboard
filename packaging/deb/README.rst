================================
 Packaging for Debian GNU/Linux
================================

The ``packaging/deb`` directory contains debian packaging of temBoard agent from
released tarball on PyPI.

Building and uploading
----------------------

The ``all`` target builds packages for every supported distributions while
``push`` targets run dput on the latest ``.changes``. Once you have setup your
host for building, just run:

::

   make all push

You may be prompted for a passphrase to open your private key. The
packages are stored in ``dist/`` at the root of the project.

Setup
-----

Package building requires Docker and Docker Compose for isolation. For signing,
you need the ``devscripts`` package and a GPG private key. For uploading, you
require ``dput``.

::

   sudo apt install devscripts dput

Ensure dput is configured to send to Dalibo Labs APT repository with the
configuration named ``labs``.

Now, export your full name and email address in ``DEBFULLNAME`` and
``DEBEMAIL`` env vars before building the packages. The maintainer field
of the package is formatted as ``$DEBFULLNAME <$DEBEMAIL>``.

``debsign`` signs ``.changes`` with the GPG signature matching the
maintainer field ``$DEBFULLNAME <$DEBEMAIL>``.

Development
-----------

First, run docker container for interactive usage:

::

   docker-compose run --rm stretch /bin/bash

If you get no output just after the run, type ``ENTER`` or ``CTRL+L`` to
redraw.

Top srcdir is mounted as ``/workspace/`` and ``dist/`` is mounted as ``/dist/``.
Just call ``/workspace/packaging/deb/mkdeb.sh`` to build debian package from
PYPI. Use `FROMSOURCE=1` to build the package from source tree.

Once you quit the shell, the container is destroyed.
