Installation from RPM on RHEL6 and later
========================================

RHEL / CentOS 6/7
-----------------

Install the ``dalibo-labs`` package with GPG key and .repo from https://yum.dalibo.org/labs/dalibo-labs-1-1.noarch.rpm

.. code-block:: bash

   sudo yum install -y https://yum.dalibo.org/labs/dalibo-labs-1-1.noarch.rpm
   sudo yum makecache fast
   sudo yum repolist


You can also setup YUM manually with the following snippet in ``/etc/yum.repos.d/dalibolabs.repo``:

.. code-block:: ini

    [dalibolabs]
    name=Dalibo Labs - CentOS/RHEL $releasever - $basearch
    baseurl=https://yum.dalibo.org/labs/CentOS$releasever-$basearch
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
