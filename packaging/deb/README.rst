============================
 Packaging Debian GNU/Linux
============================


First, export your full name and email address in ``DEBFULLNAME`` and
``DEBEMAIL`` env vars. The maintainer field of the package is formatted as
``$NAME <$EMAIL>``.

Then, once your host is setup, trigger build and upload with ``make all push``.

The ``build`` target builds packages for every supported Debian variant.
``push`` uploads packages to dput configuration named ``labs``. The packages are
stored in ``dist/`` relative to the root of the project.


Setup
-----

The ``mkdeb.sh`` script builds ``.deb`` for the latest version on PyPI. The
``Makefile`` uses docker to isolate the build environment.

``make deb-$CODENAME`` build the .deb for a specific debian distribution
release: ``stretch``, ``sid``, or any other Debian distribution available at
https://hub.docker.com/_/buildpack-deps/.

debsign signs ``.changes`` with the GPG signature matching the maintainer field
``$NAME <$EMAIL>``. You may be prompted for a passphrase to open your private
key.

::

    CODENAME=stretch make debsign
    make[1] : on entre dans le répertoire « /home/bersace/src/dalibo/temboard-dev/packaging »
    find ../dist/$CODENAME -name "*.changes" | xargs -rt debsign --no-re-sign
    debsign --no-re-sign ../dist/stretch/temboard_1.0~a1-0dlb1_amd64.changes
     signfile changes ../dist/stretch/temboard_1.0~a1-0dlb1_amd64.changes XXX <XXX@XXX>

    Successfully signed changes file

temBoard depends only on Python. All dependencies are bundled. You can easily
install the package with a simple ``dpkg -i ../dist/stretch/temboard*.deb``.


Development
-----------

Run docker image for interactive usage:

.. code-block::

   CODENAME=buster docker-compose run --rm debian /bin/bash

``packaging/`` is mounted as ``/workspace/`` and ``dist/`` is mounted as
``/dist/``. Just call ``/workspace/mkdeb.sh`` to build debian package. The
output is stored in ``/dist/$CODENAME/``.

.. notice:: If you get no output just after the run, type ``ENTER`` or
            ``CTRL+L`` to redraw.

Once you quit the shell, the container is destroyed.

.. _FPM: https://github.com/jordansissel/fpm
