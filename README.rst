################
 temBoard Agent
################

| |Python| |CircleCI| |RTD| |PyPI| |Docker|

temBoard_ is a powerful management tool for PostgreSQL.

temBoard agent is a Python service designed to run along PostgreSQL, exposing a
REST API to implement various management tasks on PostgreSQL instance. See
http://temboard.io/ for the big picture.


==========
 Features
==========

- Non intrusive daemon dedicated to one PostgreSQL cluster.
- No extra dependencies.
- Written python2.6 and python3, supported by stable distribution releases.
- Secured REST API with SSL and credentials.
- Extensible with plugins.


==============
 Installation
==============

See `temBoard documentation`_ for available installation methods and details on
configuration.


.. |CircleCI| image:: https://circleci.com/gh/dalibo/temboard-agent.svg?style=shield
   :target: https://circleci.com/gh/dalibo/temboard-agent
   :alt: CircleCI

.. |Docker| image:: https://img.shields.io/docker/automated/dalibo/temboard-agent.svg
   :target: https://hub.docker.com/r/dalibo/temboard-agent/
   :alt: Docker image available

.. |PyPI| image:: https://img.shields.io/pypi/v/temboard-agent.svg
   :target: https://pypi.python.org/pypi/temboard-agent
   :alt: Version on PyPI

.. |Python| image:: https://img.shields.io/pypi/pyversions/temboard-agent.svg
   :target: https://www.python.org/
   :alt: Versions of python supported

.. |RTD| image:: https://readthedocs.org/projects/temboard-agent/badge/?version=latest
   :target: http://temboard-agent.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation

.. _`temBoard`: http://temboard.io/
.. _`temBoard documentation`: http://temboard.readthedocs.io/
