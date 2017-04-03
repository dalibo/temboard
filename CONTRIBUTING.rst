################################
 Contributing to temBoard Agent
################################

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
