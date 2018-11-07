##############
 Contributing
##############


Reporting Issue & Submitting a Patch
====================================

We use `dalibo/temboard-agent <https://github.com/dalibo/temboard-agent>`_ to
track issue and review contribution. Fork the main repository and open a PR
against ``master`` as usual.


Docker Development Environment
==============================

With Docker & Compose, you can run your code like this:

.. code-block:: console

   $ docker-compose up -d
   $ docker-compose exec agent bash
   # pip install -e /usr/local/src/temboard-agent/
   # sudo -u postgres temboard-agent

Goto https://0.0.0.0:8888/ to add your instance with address ``agent``, port
``2345`` and key ``key_for_agent_dev``.

That's it !

The ``make shell`` target is a shorthand to ``docker-compose exec agent bash``
if you prefer.


Editing Documentation
=====================

Sphinx generates temBoard agent documentation.

.. code-block:: console

   $ cd docs/
   $ pip install -r requirements-doc.txt
   $ make watch

Now run ``make serve`` in another terminal and point your web browser at
http://0.0.0.0:8000/. There is no auto-refresh.


Releasing
=========

Releasing a new version of temBoard agent requires write access to master on
`main repository <https://github.com/dalibo/temboard-agent>`_, `PyPI project
<https://pypi.org/project/temboard-agent>`_ and `Docker Hub repository
<https://hub.docker.com/r/dalibo/temboard-agent>`_.

For the tooling, you need Git 1.8+, a recent setuptools with wheel, and twine.
For debian packaging, see below.

Please follow these steps:

- Checkout the release branch, e.g. v2.
- Choose the next version according to `PEP 440
  <https://www.python.org/dev/peps/pep-0440/#version-scheme>`_ .
- Update ``temboardagent/version.py``, without committing.
- Generate commit and tag with ``make release``.
- Push Python egg to PyPI using ``make upload``.
- Build and push RPM packages using ``make -C packaging/rpm all push``.
- Build and push debian packages using ``make -C packaging/deb all push``.
- Trigger docker master build from
  https://hub.docker.com/r/dalibo/temboard-agent/~/settings/automated-builds/.


Other documentation for maintainers
===================================

.. toctree::
   :maxdepth: 1

   packaging-deb
   packaging-rpm
