.. _temboard-agent-upgrade:

Upgrade (RHEL/CentOS)
=====================

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
