==============
 Installation
==============

This page document a quick way of installing the agent. For production system,
you may want to use trusted certificate and other enhancement.


Prerequisites
=============

In order to run temBoard agent, you require:

- PostgreSQL 9.4+, listening on UNIX socket, on the same host. Check with ``sudo -u postgres psql``.
- openssl.
- Python 2.6+ or 3.5+. Check with ``python --version``.
- A running temBoard UI.
- bash and sudo for setup script.


Now choose the method matching best your target environment.

.. raw:: html

   <ul class="tabs">
     <li><a href="#debian"><img src="_static/debian.svg" height="48" width="48"></img> Debian</a></li>
     <li><a href="#rhel-centos"><img src="_static/centos.svg" height="48" width="48"></img> RHEL / CentOS</a></li>
     <li><a href="#pypi"><img src="_static/pypi.svg" height="48" width="48"></img> PyPI</a></li>
   </ul>


Debian
======

temBoard debs are published on `Dalibo Labs APT repository
<https://apt.dalibo.org/labs/>`_. temBoard agent supports Debian stretch, jessie
and wheezy. Start by enabling Dalibo Labs APT repository.

.. code-block:: console

   # echo deb http://apt.dalibo.org/labs $(lsb_release -cs)-dalibo main > /etc/apt/sources.list.d/dalibo-labs.list
   # curl https://apt.dalibo.org/labs/debian-dalibo.asc | apt-key add -
   # apt update -y  # You may use apt-get here.

You can install now temBoard agent with:

.. code-block:: console

   # apt install temboard-agent
   # temboard-agent --version


RHEL / CentOS
=============

temBoard RPM are published on `Dalibo Labs YUM repository
<https://yum.dalibo.org/labs/>`_. temBoard agent supports RHEL / CentOS 6 and 7.
Start by enabling Dalibo Labs YUM repository.

.. code-block:: console

   $ sudo yum install -y https://yum.dalibo.org/labs/dalibo-labs-2-1.noarch.rpm
   $ sudo yum makecache fast

.. warning::

    Do **NOT** use temBoard agent rpm from PGDG. They are known to be broken.


With the YUM repository configured, you can install temBoard agent with:

.. code-block:: console

   $ sudo yum install temboard-agent
   $ temboard-agent --version


PyPI
====

temBoard agent wheel and source tarball are published on `PyPI
<https://pypi.org/project/temboard-agent>`_.

Installing from PyPI requires Python2.6+, pip and wheel. It's better to have a
recent version of pip. For Python 2.6, you will need some backports libraries.

.. code-block:: console

    $ sudo pip install temboard-agent
    $ sudo pip2.6 install logutils argparse  # Only for Python 2.6
    $ temboard-agent --version

Note where is installed temBoard agent and determine the prefix. You must find a
``share/temboard-agent`` folder in e.g ``/usr`` or ``/usr/local``. If temBoard
agent is installed in ``/usr/local``, please adapt the documentation to match
this system prefix.


.. raw:: html

   <script src="_static/tabs.js" defer="defer"></script>
   <style type="text/css">
   .tabs {
     text-align: center;
     margin: 0;
     padding: 0;
     display: flex;
     flex-flow: row nowrap;
     justify-content: center;
     align-items: flex-start;
   }

   .rst-content .section ul.tabs li {
     display: block;
     flex-grow: 1;
     margin: 0;
     padding: 4px;
   }

   .tabs li + li {
     border-left: 1px solid black;
   }

   .tabs li img {
     margin: 8px auto;
     display: block;
   }

   .tabs li a {
     display: inline-block;
     width: 100%;
     padding: 4px;
     font-size: 110%;
   }

   .tabs li a.active {
     font-weight: bold;
     /* Match RTD bg of current entry in side bar. */
     background: #e3e3e3;
   }
   </style>


Setup one instance
==================

To finish the installation, you will need to follow the next steps for each
Postgres instance on the host:

- *configure* the agent;
- *add a first user*;
- *start* the agent;
- finally *register* it in the UI.

The quickest way to setup temBoard agent is to use the ``auto_configure.sh``
script, installed in ``/usr/share/temboard-agent``.

You must run this script as root, with ``PG*`` env vars set to connect to the
Postgres cluster you want to manage. By default, the script uses ``postgres``
UNIX user to connect to Postgres cluster. The script receive the temBoard UI URL
as single required argument.

.. note::

   Each agent is identified by the fully qualified *hostname*. If ``hostname
   --fqdn`` can't resolve the FQDN of your HOST, just overwrite it using
   ``TEMBOARD_HOSTNAME`` envvar. Remember that ``localhost`` or event a short
   hostname is not enough. ``auto_configure.sh`` enforce this.

.. code-block:: console

   # /usr/share/temboard-agent/auto_configure.sh https://temboard-ui.lan:8888

The script show you some important informations for the next steps:

- the path to the main configuration file like
  ``/etc/temboard-agent/11/main/temboard-agent.conf``.
- TCP port like 2345.
- secret key for registration like ``d52cb5d39d265f03ae570e1847b90e10``.

You will need these informations later. Keep them near. Now add a first user
using ``temboard-agent-adduser``:

.. code-block:: console

   # sudo -u postgres temboard-agent-adduser -c /etc/temboard-agent/11/main/temboard-agent.conf

Adapt the configuration file to match the one created by ``auto_configure.sh``.
Later, when the agent has been registered, you will need to authenticate against
the agent with this user, right from the UI.

Now start the agent using the command suggested by ``auto_configure.sh``. On
most systems now, it's a systemd service:

.. code-block:: console

   # systemctl start temboard-agent@11-main

Now you can register the agent in the UI using ``temboard-agent-register``:

.. code-block:: console

   # sudo -u postgres temboard-agent-register -c /etc/temboard-agent/11/main/temboard-agent.conf --host $(hostname --fqdn) --port 2345 --groups default https://temboard-ui.lan:8888

Don't forget to adapt this command line to your case. Configuration file, port
and temBoard UI address are likely to change from one installation to another.
``tembord-agent-register`` will ask you to login to the UI. Beware, it is
**NOT** the user on the agent.


It's up !
=========

Congratulation ! You can continue on the UI on see the agent appeared, and
monitoring data being graphed.

You can repeat the setup one instance for each instance on the same host.
