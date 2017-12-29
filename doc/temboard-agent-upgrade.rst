.. _temboard-agent-upgrade:

Upgrade process (RHEL/CentOS)
=============================

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
