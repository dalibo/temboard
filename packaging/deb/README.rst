================================
 Packaging for Debian GNU/Linux
================================

This directory contains debian packaging of temBoard agent from released tarball
an PyPI.

Building and uploading
======================

The ``build`` target builds **all** packages for every supported distributions.
Once you have setup your host for building, just run:

.. code-block::

   make build dput

You may be prompted for a passphrase to open your private key. The packages are
stored in ``dist/`` at the root of the project.


Setup
=====

Package building requires Docker and Docker Compose for isolation. For .deb
building, you need the ``devscripts`` package on debian and GPG to sign package.

.. code-block::

   sudo apt install devscripts


Now, export your full name and email address in ``DEBFULLNAME`` and ``DEBEMAIL``
env vars. The maintainer field of the package is formatted as ``$DEBFULLNAME
<$DEBEMAIL>``.

``debsign`` signs ``.changes`` with the GPG signature matching the maintainer
field ``$DEBFULLNAME <$DEBEMAIL>``.


Development
===========

Run docker container for interactive usage:

.. code-block::

   docker-compose run --rm stretch /bin/bash

``deb/`` is mounted as ``/workspace/`` and ``dist/`` is mounted as
``/dist/``. Just call ``/workspace/mkdeb.sh`` to build debian package.

If you get no output just after the run, type ``ENTER`` or ``CTRL+L`` to redraw.

Once you quit the shell, the container is destroyed.
