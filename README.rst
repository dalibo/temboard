################
 temBoard Agent
################

| |CircleCI|

`temBoard <http://temboard.io/>`_ is a powerful management tool for PostgreSQL.

temBoard agent is a Python2 service designed to run along PostgreSQL, exposing a
REST API to implement various management tasks on PostgreSQL instance. See
http://temboard.io/ for the big picture.


============
 Developing
============

With Docker & Compose, you can run your code like this:

.. code-block::

   $ docker-compose up -d
   $ docker-compose exec agent bash
   # pip install -e /usr/local/src/temboard-agent/
   # gosu temboard temboard-agent -c temboard-agent.conf

Goto https://0.0.0.0:8888/ to add your agent with hostname ``agent`` and port
``2345``.

That's it !


===========
 Releasing
===========

Choose the next version according to `PEP 440
<https://www.python.org/dev/peps/pep-0440/#version-scheme>`_.

.. code-block

   git tag 1.1
   git push --tags
   make release


.. |CircleCI| image:: https://circleci.com/gh/dalibo/temboard-agent.svg?style=shield
   :target: https://circleci.com/gh/dalibo/temboard-agent
   :alt: CircleCI
