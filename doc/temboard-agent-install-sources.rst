Installation from sources
=========================

Dependencies
------------

  - ``python`` **2.7**
  - ``python-setuptools`` >= **0.6**

Installation
------------

First install Python ``setuptools`` with ``pip``:

.. code-block:: bash

    sudo pip install setuptools

Proceed with the installation of the agent:

.. code-block:: bash

    cd temboard-agent/
    sudo pip install .


Prepare directories and files
-----------------------------

Creation of directories for configuration and SSL files:

.. code-block:: bash

    sudo mkdir /etc/temboard-agent

Home directory:

.. code-block:: bash

    sudo mkdir /var/lib/temboard-agent
    sudo mkdir /var/lib/temboard-agent/main

Logging directory:

.. code-block:: bash

    sudo mkdir /var/log/temboard-agent

Copy the sample configuration file:

.. code-block:: bash

    sudo cp /usr/share/temboard-agent/temboard-agent.conf /etc/temboard-agent/temboard-agent.conf

Copy the logrotate configuration file:

.. code-block:: bash

    sudo cp /usr/share/temboard-agent/temboard-agent.logrotate /etc/logrotate.d/temboard-agent

Change owner and rights:

.. code-block:: bash

    sudo chown -R postgres:postgres /var/lib/temboard-agent
    sudo chown postgres:postgres /var/log/temboard-agent
    sudo chown -R postgres:postgres /etc/temboard-agent
    sudo chmod 0600 /etc/temboard-agent/temboard-agent.conf


Configuration
-------------

Before starting the agent, see :ref:`temboard-agent-configuration` for post-installation tasks.

Operating the agent
-------------------

Start
^^^^^

.. code-block:: bash

    sudo -u postgres temboard-agent -d -p /var/lib/temboard-agent/main/temboard-agent.pid

Stop
^^^^

.. code-block:: bash

    sudo kill $(cat /var/lib/temboard-agent/main/temboard-agent.pid)

Reload configuration
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo kill -HUP $(cat /var/lib/temboard-agent/main/temboard-agent.pid)

Smoke test
----------

Start the agent, then try:

.. code-block:: bash

    curl -k https://127.0.0.1:2345/discover
    curl -k -X POST -H "Content-Type: application/json" -d '{"username": "<username>", "password": "<password>"}' https://127.0.0.1:2345/login
