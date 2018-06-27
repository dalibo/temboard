=======================================
 Packaging for GNU/Linux distributions
=======================================

Package building requires Docker and Docker Compose for isolation. For .deb
building, you need the ``devscripts`` package on debian and GPG to sign package.

.. code-block::

   sudo apt install devscripts


Now, export your full name and email address in ``DEBFULLNAME`` and ``DEBEMAIL``
env vars. The maintainer field of the package is formatted as ``$DEBFULLNAME
<$DEBEMAIL>``.

The ``build`` target builds **all** packages for every supported distributions.

.. code-block::

   make build

The packages are stored in ``dist/`` relative to the root of the project.


For Debian
==========

The ``mkdeb.sh`` script builds ``.deb`` for the latest version on PyPI. The
``Makefile`` uses docker to isolate the build environment. ``make deb`` builds
one .deb portable accross supported Debian distribution release.

``debsign`` signs ``.changes`` with the GPG signature matching the maintainer
field ``$DEBFULLNAME <$DEBEMAIL>``. You may be prompted for a passphrase to open
your private key.

Here is a sample output of build log tail::

    ...
    Purging configuration files for temboard-agent (1.0~a2-0dlb1) ...
    dpkg: warning: while removing temboard-agent, directory '/usr/lib/systemd/system' not empty so not removed
    make changes-stretch
    make[1]: Entering directory '/home/src/dalibo/temboard-agent-wip/deb'
    ./mkchanges.sh /home/src/dalibo/temboard-agent-wip/dist/temboard-agent_1.0~a2-0dlb1_all.deb stretch
    DEBUG    Working in /tmp/tmpK0U50r.
    INFO     Extracting control file.
    DEBUG    Cleaning /tmp/tmpK0U50r.
    INFO     .changes generated for /home/src/dalibo/temboard-agent-wip/dist/temboard-agent_1.0~a2-0dlb1_all.deb.
     signfile changes /home/src/dalibo/temboard-agent-wip/dist/temboard-agent_1.0~a2-0dlb1_all_stretch.changes Étienne BERSAC <etienne.bersac@dalibo.com>

    Successfully signed changes file
    make[1]: Leaving directory '/home/src/dalibo/temboard-agent-wip/deb'


temBoard agent depends only on Python2.7. You can easily install the package
with a simple ``dpkg -i ../dist/temboard-agent*.deb``.


Development of Debian packaging
-------------------------------

Run docker container for interactive usage:

.. code-block::

   docker-compose run --rm debian /bin/bash

``deb/`` is mounted as ``/workspace/`` and ``dist/`` is mounted as
``/dist/``. Just call ``/workspace/mkdeb.sh`` to build debian package.

If you get no output just after the run, type ``ENTER`` or ``CTRL+L`` to redraw.

Once you quit the shell, the container is destroyed.


APT test repository
-------------------

``make reprepro`` setup a naïve APT repository. Ensure you have ``.docker``
resolution with either dnsdock_ or libnss-docker_. You can then test upload and
download of the package.

.. code-block::

   $ dput -c dput.cf stable ../dist/jessie/temboard*.changes
   Checking signature on .changes
   gpg: ../dist/jessie/temboard-agent_1.0~a1-0dlb1_all.changes: Valid signature from 95997557AD5A6DBF
   Uploading to stable (via scp to temboard-incoming.docker):
   Could not chdir to home directory /home/reprepro: No such file or directory
   temboard-agent_1.0~a1-0dlb1_all.deb                                                    100%  168KB  10.5MB/s   00:00
   temboard-agent_1.0~a1-0dlb1_all.changes                                                100% 1307     1.2MB/s   00:00
   Successfully uploaded packages.
   Could not chdir to home directory /home/reprepro: No such file or directory
   Could not check validity of signature with '95997557AD5A6DBF' in 'temboard-agent_1.0~a1-0dlb1_all.changes' as public key missing!
   Skipping temboard-agent_1.0~a1-0dlb1_all.changes because all packages are skipped!
   $ curl http://temboard-repository.docker/debian/dists/jessie/main/binary-amd64/Packages
   Package: temboard-agent
   Version: 1.0~a1-0dlb1
   License: PostgreSQL
   Vendor: contact@dalibo.com
   ...

Use ``deb http://temboard-repository.docker/debian jessie main`` in
``sources.list`` to test it with APT.

.. code-block::

    # echo deb http://temboard-repository.docker/debian $(lsb_release -sc) main >/etc/apt/sources.list.d/temboard.list
    # apt-key add path/to/temboard-agent/deb/reprepro-config/reprepro_pub.gpg
    # apt-get update -y
    # apt-cache policy temboard-agent
    temboard-agent:
      Installed: (none)
      Candidate: 1.0~a1-0dlb1
      Version table:
         1.0~a1-0dlb1 0
            500 http://nginx.docker/debian/ jessie/main amd64 Packages
    # apt-get install temboard-agent
    Reading package lists... Done
    Building dependency tree
    Reading state information... Done
    The following NEW packages will be installed:
      temboard-agent
    0 upgraded, 1 newly installed, 0 to remove and 15 not upgraded.
    Need to get 172 kB of archives.
    After this operation, 691 kB of additional disk space will be used.
    Get:1 http://temboard-repository.docker/debian/ wheezy/main temboard-agent all 1.0~a1-0dlb1 [172 kB]
    Fetched 172 kB in 0s (0 B/s)
    debconf: delaying package configuration, since apt-utils is not installed
    Selecting previously unselected package temboard-agent.
    (Reading database ... 17656 files and directories currently installed.)
    Unpacking temboard-agent (from .../temboard-agent_1.0~a1-0dlb1_all.deb) ...
    Setting up temboard-agent (1.0~a1-0dlb1) ...
    #

Use ``make reprepro-trash`` to reset the test repository.

.. _dnsdock: https://github.com/aacebedo/dnsdock
.. _libnss-docker: https://github.com/danni/docker-nss/
