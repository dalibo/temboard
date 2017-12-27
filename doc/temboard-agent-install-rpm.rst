Installation from RPM on RHEL6 and later
========================================

RHEL / CentOS 6
---------------

Install the ``packages.temboard.io`` repository by creating the ``/etc/yum.repos.d/temboard.repo`` file with the following content:

.. code-block:: ini

    [temboard]
    name=temBoard Packages for Enterprise Linux 6
    baseurl=https://packages.temboard.io/yum/rhel6/
    enabled=1
    gpgcheck=0


RHEL / CentOS 7
---------------

Install the ``packages.temboard.io`` repository by creating the ``/etc/yum.repos.d/temboard.repo`` file with the following content:

.. code-block:: ini

    [temboard]
    name=temBoard Packages for Enterprise Linux 7
    baseurl=https://packages.temboard.io/yum/rhel7/
    enabled=1
    gpgcheck=0


Package installation
--------------------

.. code-block:: ini

   sudo yum install temboard-agent


Configuration
-------------

Before starting the agent, see :ref:`temboard-agent-configuration` for post-installation tasks.


Firewall
--------

Warning, on RHEL/CentOS, TCP port filtering is enabled by default. TCP port the agent is listening on must be open (``2345`` by default).

RHEL / Centos 6
^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo iptables -I INPUT -p tcp -m tcp --dport 2345 -j ACCEPT
    sudo service iptables save


RHEL / Centos 7
^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo firewall-cmd --permanent --add-port=2345/tcp
    sudo firewall-cmd --reload


Operating the agent on RHEL / CentOS 6
--------------------------------------


Start
^^^^^

.. code-block:: bash

    sudo service temboard-agent start


Stop
^^^^

.. code-block:: bash

    sudo service temboard-agent stop


Restart
^^^^^^^

.. code-block:: bash

    sudo service temboard-agent restart


Reload
^^^^^^

.. code-block:: bash

    sudo service temboard-agent reload


Start at boot time
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo chkconfig temboard-agent on


Operating the agent on RHEL / CentOS 7
--------------------------------------


Start
^^^^^

.. code-block:: bash

    sudo systemctl start temboard-agent


Stop
^^^^

.. code-block:: bash

    sudo systemctl stop temboard-agent


Restart
^^^^^^^

.. code-block:: bash

    sudo systemctl restart temboard-agent


Reload
^^^^^^

.. code-block:: bash

    sudo systemctl restart temboard-agent


Start at boot time
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo systemctl enable temboard-agent
