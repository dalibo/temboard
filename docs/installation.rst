==============
 Installation
==============

This page document a quick way of installing the agent. For production system,
you may want to use trusted certificate and other enhancement.


Prerequisites
=============

In order to run temBoard agent, you need:

- Linux as underlying OS.
- PostgreSQL 9.4+, listening on UNIX socket. Check with ``sudo -u postgres psql``.
- openssl.
- Python 2.6+ or 3.5+. Check with ``python --version``.
- A running temBoard UI.
- bash, curl and sudo for setup script.

.. note::

  The temBoard agent must run on the same host as the PostgreSQL instance. Running an agent on a remote host is not yet supported.


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
UNIX user to connect to Postgres cluster. The script receives the temBoard UI URL
as single required argument.

.. note::

   Each agent is identified by the fully qualified *hostname*. If ``hostname
   --fqdn`` can't resolve the FQDN of your HOST, simply overwrite it using
   ``TEMBOARD_HOSTNAME`` envvar. Remember that ``localhost`` or even a short
   hostname is not enough. ``auto_configure.sh`` enforces this.

.. code-block:: console

   # /usr/share/temboard-agent/auto_configure.sh https://temboard-ui.lan:8888

The script shows you some important information for the next steps:

- the path to the main agent configuration file like
  ``/etc/temboard-agent/11/main/temboard-agent.conf``

.. note::

  Some parts of the
  configuration are in ``/etc/temboard-agent/11/main/temboard-agent.conf.d/auto.conf``
  too and override the main configuration file.

- agent TCP port (usually 2345 if this is your first agent on this host)
- secret key for registration like ``d52cb5d39d265f03ae570e1847b90e10``.

You will need these information later. Keep them near. Now create a first user
(specific to this agent) using ``temboard-agent-adduser``.
Later, once the agent is registered, you will need to authenticate against
the agent with this user from the UI to interact with the agent.

.. code-block:: console

   # sudo -u postgres temboard-agent-adduser -c /etc/temboard-agent/11/main/temboard-agent.conf

Adapt the configuration file name to match the one created by ``auto_configure.sh``.

Now start the agent using the command suggested by ``auto_configure.sh``. On
most systems now, it's a systemd service:

.. code-block:: console

   # systemctl start temboard-agent@11-main

Check that it has started successfully:

.. code-block:: console

   # systemctl status temboard-agent@11-main

Now you can register the agent in the UI using ``temboard-agent-register``.
It needs the configuration file path, the agent host and port and the path
to the temBoard UI.:

.. code-block:: console

   # sudo -u postgres temboard-agent-register -c /etc/temboard-agent/11/main/temboard-agent.conf --host $(hostname --fqdn) --port 2345 --groups default https://temboard-ui.lan:8888

``temboard-agent-register`` will ask you to login to the UI
(eg. ``admin`` if you've kept the default temBoard user).
Beware, it is **NOT** the user set on the agent.


It's up!
========

Congratulation! You can continue on the UI and see the agent appeared, and
monitoring data being graphed.

You can repeat the above setup for each instance on the same host.
