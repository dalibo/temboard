| |temBoard|

Monitor, optimize and configure multiple PostgreSQL instances.

| |PyPI| |Python| |CircleCI| |RTD|

| |Demo|


=========
 Install
=========

temBoard is composed of two services:

- A lightweight **agent** that you need to install on every PostgreSQL server
  you want to manage.
- A central **web app** to control the agents and collect metrics.

temBoard project provides packages for RHEL and clones as well as Debian. See
`temboard.readthedocs.io <http://temboard.readthedocs.io/en/latest/>`_ for
installation instructions.


===================
 Docker Quickstart
===================

We provide a complete *testing* environment based on Docker ! Please read our
`QUICKSTART <https://github.com/dalibo/temboard/blob/master/QUICKSTART.md>`_
guide for more details.


============
 Contribute
============

temBoard is an open project. Any contribution to improve it is welcome.

Want to contribute? Please first read our guide on `contributing
<https://github.com/dalibo/temboard/blob/master/CONTRIBUTING.md>`_ if you're
interested in getting involved.


=========
 License
=========

temBoard is available under the `PostgreSQL License
<https://github.com/dalibo/temboard/blob/master/LICENSE>`_.


.. |CircleCI| image:: https://circleci.com/gh/dalibo/temboard.svg?style=shield
   :target: https://circleci.com/gh/dalibo/temboard
   :alt: CircleCI

.. |Demo| image:: https://github.com/dalibo/temboard/raw/master/docs/sc/instance-dashboard.png
   :target: https://labs.dalibo.com/temboard
   :alt: Screenshot temBoard

.. |PyPI| image:: https://img.shields.io/pypi/v/temboard.svg
   :target: https://pypi.python.org/pypi/temboard
   :alt: Version on PyPI

.. |Python| image:: https://img.shields.io/pypi/pyversions/temboard.svg
   :target: https://www.python.org/
   :alt: Versions of python supported

.. |RTD| image:: https://readthedocs.org/projects/temboard/badge/?version=latest
   :target: https://temboard.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation

.. |temBoard| image:: https://github.com/dalibo/temboard/raw/master/docs/temboard.png
   :target: http://labs.dalibo.com/temboard/
   :alt: temBoard logo: a bird
