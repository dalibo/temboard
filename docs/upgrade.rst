.. _temboard-agent-upgrade:

Upgrade (RHEL/CentOS)
=====================

6.X to 7.0
----------

First of all, beware that support for ``RHEL/CentOS 6`` has been dropped.

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent

Update the package:

.. code-block:: bash

    sudo yum install temboard-agent

Load the ``pg_stat_statements`` extension on the Postgres instance you are
monitoring with the agent. Please refer to the
`official documentation <https://www.postgresql.org/docs/current/pgstatstatements.html>`_.

Notes:
  - You may need to install the PostgreSQL contrib package;
  - You will need to restart the instance.

Enable the extension. Make sure you enable the extension on the database set in
the agent configuration.

.. code-block:: SQL

    CREATE EXTENSION pg_stat_statements;

Update configuration file ``/etc/temboard-agent/temboard-agent.conf`` to add
the ``statements`` plugin.

Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


5.X to 6.0
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


4.X to 5.0
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


3.X to 4.0
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


2.X to 3.0
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Load the maintenance plugin by adding "maintenance" in the list of plugins in your temboard-agent.conf file.


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


1.2 to 2.0
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install python-setuptools
    sudo yum install temboard-agent


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


1.1 to 1.2
----------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent


0.0.1 to 1.1
------------

Stop the agent:

.. code-block:: bash

    sudo systemctl stop temboard-agent


Update the package:

.. code-block:: bash

    sudo yum install temboard-agent


Update configuration file ``/etc/temboard-agent/temboard-agent.conf``:

 - ``supervision`` plugin name must be replaced by ``monitoring``
 - ``settings`` plugin name must be replaced by ``pgconf``
 - CA cert. file usage is not mandatory anymore, parameter ``ssl_ca_cert_file`` can be commented


Start the agent:

.. code-block:: bash

    sudo systemctl start temboard-agent
