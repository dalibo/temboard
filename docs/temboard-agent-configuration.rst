.. _temboard-agent-configuration:

Configuration
=============

Key & Hostname
--------------

In the ``temboard-agent.conf`` file, 2 important parameters must be configured to make the agent interact with the central server:

* The ``hostname`` is used to identify the Agent. It must be a **unique** and
  `fully qualified domain name <https://en.wikipedia.org/wiki/Fully_qualified_domain_name>`_ ( e.g. ``db1.mydomain.foo`` ).
  Note that ``localhost`` is not a valid value for this parameter.

* The ``key`` is used to authenticate the Agent. It must be a long series of characters and you must keep it secret. The best
  way to configure the agent key is to generate a random string of letters and digits:

.. code-block:: bash

    cat /dev/urandom | tr -dc '[:alnum:]' | fold -w 64 | head -1


SSL certificate
---------------

``temboard-agent`` embeds a lightweight HTTPS server aimed to serve its API, thus it is required to use a SSL certificate. As long as the agent's API is not reachable through a public interface, usage of self-signed certificates is safe.

When the agent is installed from RPM package, a new SSL self-signed cert. is built.

Using provided SSL certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It provides a ready to use self-signed SSL certifcate located in ``/usr/share/temboard-agent/quickstart`` directory, if you don't want to use it, you can create a new one with the ``openssl`` binary.


.. code-block:: bash

    sudo cp /usr/share/temboard-agent/quickstart/temboard-agent_CHANGEME.key /etc/temboard-agent/.
    sudo cp /usr/share/temboard-agent/quickstart/temboard-agent_CHANGEME.pem /etc/temboard-agent/.
    sudo chown postgres:postgres /etc/temboard-agent/*


Build a new self-signed certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build a new SSL certifcate:

.. code-block:: bash

    sudo -u postgres openssl req -new -x509 -days 365 -nodes -out /etc/temboard-agent/localhost.pem -keyout /etc/temboard-agent/localhost.key

Then, ``ssl_cert_file`` and ``ssl_key_file`` parameters from ``temboard-agent.conf`` file need to be set respectively to ``localhost.pem`` and ``localhost.key``.

CA certificate file
^^^^^^^^^^^^^^^^^^^

``monitoring`` plugin sends data to the collector (API served by the temBoard UI web server) through HTTPS. If you want to enable SSL cert. check (THIS IS NOT MANDATORY), HTTPS client implemented by the agent needs to have UI's SSL certifcate (.pem) stored in its CA certificate file. temBoard agent embeds a default CA cert. file containing default temBoard UI SSL certificate.

.. code-block:: bash

    sudo cp /usr/share/temboard-agent/quickstart/temboard-agent_ca_certs_CHANGEME.pem /etc/temboard-agent/ca_certs_localhost.pem

``ssl_ca_cert_file`` parameter in section ``[monitoring]`` from the configuration file needs to be set to ``ca_certs_localhost.pem``.

If you don't want to enable SSL cert. check, please comment ``ssl_ca_cert_file`` parameter.

Restrictions on SSL files
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo chmod 0600 /etc/temboard-agent/*.key
    sudo chmod 0600 /etc/temboard-agent/*.pem

Access to PostgreSQL Cluster
----------------------------

The agent needs a PostgreSQL superuser. By default, it is configured to work with ``postgres`` user.

To create a dedicated one with password authentication:

.. code-block:: bash

    sudo -u postgres createuser temboard -s -P

This superuser should be able to connect to the cluster through the unix socket using a password, check ``pg_hba.conf`` file and reload configuration.
Example of ``pg_hba.conf`` entry: ::

    local   postgres        temboard                                  md5

The access to the PostgreSQL cluster is then configured in the ``[postgresql]`` section of the ``/etc/temboard-agent/temboard-agent.conf`` file.

Users
-----

When interacting with the agent using HTTP, for example when accessing certain pages in the Web UI, an authentication is required. Accounts are created using the tool: ``temboard-agent-adduser``.

Add a first user:

.. code-block:: bash

    sudo -u postgres temboard-agent-adduser

Monitoring plugin
-----------------

If you plan to use the plugin ``monitoring``, you need to setup ``collector_url`` parameter. It lets the agent know where to post its data.
Just change the hostname to point to the server. Since the Server is only reachable using HTTPS and if you want to enable SSL cert. check,
the UI SSL certificate (or CA certificates that has issued it) must be in the filepath where ``ssl_ca_cert_file`` points.

Exemple:

.. code-block:: ini

    [monitoring]
    collector_url = https://<temboard-ui-addr>:8888/monitoring/collector



Registration
------------

Once the agent configuration is ready you can start it and proceed with its registration into the ``temboard`` web UI.

Registration can be done in two ways :

  - through ``temboard`` web UI as an administrator : `Settings` -> `Instance` -> `New instance`
  - using ``temboard-agent-register`` script from the host running ``temboard-agent``


``temboard-agent-register``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This script should help administrators to register freshly new installed agents into ``temboard`` web UI, and must be executed from the host running the agent with the same user running the agent (``postgres`` by default). It requires an administrator access to the UI (``admin`` by default).

Environment variables ``TEMBOARD_UI_USER`` and ``TEMBOARD_UI_PASSWORD`` can be used to define credentials needed to login on the web UI. If not set, credentials will be asked during script runtime.

Exemple to register the agent listening on ``<temboard-agent-addr>`` into the web UI located at ``<temboard-ui-addr>``:

.. code-block:: bash

    sudo -u postgres TEMBOARD_UI_USER="admin" TEMBOARD_UI_PASSWORD="xxxxxxx" temboard-agent-register https://<temboard-ui-addr>:8888 -h <temboard-agent-addr> -g default


Usage:

.. code-block:: bash

    usage: temboard-agent-register [-?] [-c TEMBOARD_CONFIGFILE] [-h HOST]
                                   [-p PORT] [-g GROUPS]
                                   TEMBOARD-UI-ADDRESS

    Register a couple PostgreSQL instance/agent to a Temboard UI.

    positional arguments:
      TEMBOARD-UI-ADDRESS   temBoard UI address to register to.

    optional arguments:
      -?, --help            show this help message and exit
      -c TEMBOARD_CONFIGFILE, --config TEMBOARD_CONFIGFILE
                            Configuration file
      -h HOST, --host HOST  Agent address. Default: localhost
      -p PORT, --port PORT  Agent listening TCP port. Default: 2345
      -g GROUPS, --groups GROUPS
                            Instance groups list, comma separated. Default: None


Configuration File and Directory
--------------------------------

temBoard agent reads configuration from arguments, environment and file. Defaut
configuration file is ``/etc/temboard-agent/temboard-agent.conf``. You can
change this with ``TEMBOARD_CONFIGFILE`` envvar or ``--configfile`` switch.

temBoard agent always searches for a directory whose name is constructed with
the config file and the ``.d`` suffix. Thus the default config directory is
``/etc/temboard-agent/temboard-agent.conf.d``. temBoard agent reads only files
suffixed with ``.conf``. temBoard agent reads files in POSIX sort order :
uppercase precedes lowercase.

Configuration file is mendatory while configuration directory may not exist.


The configuration file is in `INI-style format
<https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_
as implemented by Python stlib config parser. Configuration parameters are
distributed under sections:

  - ``temboard``: this is the main section grouping core parameters;
  - ``postgresql``: parameters related to the PostgreSQL cluster that the agent is connected to;
  - ``logging``: how and where to log;
  - ``dashboard``: parameters of the plugin ``dashboard``;
  - ``monitoring``: plugin ``monitoring``;
  - ``administration``: plugin ``administration``.

``temboard`` section
^^^^^^^^^^^^^^^^^^^^

  - ``port``: port number that the agent will listen on to serve its ``HTTP API``. Default: ``2345``;
  - ``address``: IP v4 address that the agent will listen on. Default: ``0.0.0.0`` (all);
  - ``users``: Path to the file containing the list of the users allowed to use the ``HTTP API``. Default: ``/etc/temboard-agent/users``;
  - ``plugins``: Array of plugin (name) to load. Default: ``["monitoring", "dashboard", "pgconf", "administration", "activity"]``;
  - ``ssl_cert_file``: Path to SSL certificate file (.pem) for the embeded HTTPS process serving the API. Default: ``/etc/temboard-agent/temboard-agent_CHANGEME.pem``;
  - ``ssl_key_file``: Path to SSL private key file. Default: ``/etc/temboard-agent/temboard-agent_CHANGEME.key``;
  - ``home``: Path to agent home directory, it contains files used to store temporary data. When running multiple agents on the same host, each agent must have its own home directory. Default: ``/var/lib/temboard-agent/main``.
  - ``hostname``: Overrides real machine hostname. Must be a valid FQDN. Default: ``None``;

``postgresql`` section
^^^^^^^^^^^^^^^^^^^^^^

  - ``host``: Path to PostgreSQL unix socket. Default: ``/var/run/postgresql``;
  - ``port``: PostgreSQL port number. Default: ``5432``;
  - ``user``: PostgreSQL user. Must be a super-user. Default: ``postgres``;
  - ``password``: User password. Default: ``None``;
  - ``dbname``: Database name for the connection. Default: ``postgres``;
  - ``instance``: Cluster name. Default: ``main``.
  - ``key``: Authentication key used to send data to the UI. Default: ``None``;

``logging`` section
^^^^^^^^^^^^^^^^^^^

  - ``method``: Method used to send the logs: ``stderr``, ``syslog`` or ``file``. Default: ``syslog``;
  - ``facility``: Syslog facility. Default: ``local0``;
  - ``destination``: Path to the log file. Default: ``/dev/log``;
  - ``level``: Log level, can be set to ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR`` or ``CRITICAL``. Default: ``INFO``.
  - ``debug``: A comma separated list of loggers to which level will be set to ``DEBUG``.

``dashboard`` plugin
^^^^^^^^^^^^^^^^^^^^

  - ``scheduler_interval``: Time interval, in second, between each run of the process collecting data used to render the dashboard. Default: ``2``;
  - ``history_length``: Number of record to keep. Default: ``150``.

``monitoring`` plugin
^^^^^^^^^^^^^^^^^^^^^

  - ``dbnames``: Database name list (comma separated) to supervise. * for all. Default: ``*``;
  - ``collector_url``: Collector URL. Default: ``None``;
  - ``probes``: List of probes to run (comma separated). * for all. Default: ``*``;
  - ``scheduler_interval``: Interval, in second, between each run of the process executing the probes. Default: ``60``;
  - ``ssl_ca_cert_file``: File where to store collector's SSL certificate. Default: ``None``.

``administration`` plugin
^^^^^^^^^^^^^^^^^^^^^^^^^

  - ``pg_ctl``: External command used to start/stop PostgreSQL. Default: ``None``.
