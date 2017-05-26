################################
 Contributing to temBoard Agent
################################

With Docker & Compose, you can run your code like this:

.. code-block::

   $ docker-compose up -d
   $ docker-compose exec agent bash
   # pip install -e /usr/local/src/temboard-agent/
   # gosu temboard temboard-agent -c /etc/temboard-agent/temboard-agent.conf

Goto https://0.0.0.0:8888/ to add your instance with address ``agent``, port
``2345`` and key ``key_for_agent_dev``.

That's it !


======================================
 Reporting Issue & Submitting a Patch
======================================

We use `dalibo/temboard-agent <https://github.com/dalibo/temboard-agent>`_ as
BTS and patch reviewing system. Fork the main repository and open a PR against
master as usual.


===========
 Releasing
===========

Choose the next version according to `PEP 440
<https://www.python.org/dev/peps/pep-0440/#version-scheme>`_.

.. code-block::

   git tag 1.1
   git push --tags
   make release

Now build distro packages with ``make -C packaging build``. Ensure you ``NAME``
and ``EMAIL`` env vars contain maintainer identification. See
``packaging/README.rst`` for further details.
