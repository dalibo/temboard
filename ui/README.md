<p align="center">
    <img src="https://github.com/dalibo/temboard/raw/master/docs/assets/temboard-logo-slogan.png" />
</p>

<p align="center">
  <strong>Monitor, optimize and configure multiple <a href="https://postgresql.org/" target="_blank">PostgreSQL</a> instances.</strong>
</p>

<p align="center">
  <a href="https://pypi.python.org/pypi/temboard" target="_blank">
    <img src="https://img.shields.io/pypi/v/temboard.svg" alt="PyPI version" />
  </a>
  <a href="https://www.python.org/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/temboard.svg" alt="Supported Python versions" />
  </a>
  <a href="https://circleci.com/gh/dalibo/temboard" target="_blank">
    <img src="https://circleci.com/gh/dalibo/temboard.svg?style=shield" alt="CI status" />
  </a>
  <a href="https://temboard.readthedocs.io/en/latest/?badge=latest" target="_blank">
    <img src="https://readthedocs.org/projects/temboard/badge/?version=latest" alt="Documentation status" />
  </a>
</p>

<p align="center">
  <img src="https://github.com/dalibo/temboard/raw/master/docs/screenshots/instance-dashboard.png" />
</p>

<p align="center">Manage your PostgreSQL instance fleet from a unique web interface.</p>


# Features

- Manage hundreds of instances in one interface.
- Fleet-wide and per-instance dashboards.
- Monitor PostgreSQL with advanced metrics.
- Manage running sessions.
- Track bloat and schedule vacuum on tables and indexes.
- Track slow queries.
- Tweak PostgreSQL configuration.


# Docker Quickstart

We provide a complete *testing* environment based on Docker ! Please
read our
[QUICKSTART](https://temboard.readthedocs.io/en/latest/quickstart/)
guide for more details.


# Install

temBoard is composed of two services:

- A lightweight **agent** that you need to install on every PostgreSQL server you want to manage.
- A central **web app** to control the agents and collect metrics.

temBoard project provides packages for RHEL and clones as well as
Debian. See
[temboard.readthedocs.io](http://temboard.readthedocs.io/en/latest/) for
installation instructions.


# Contribute

temBoard is an open project. Any contribution to improve it is welcome.

Want to contribute? Please first read our guide on
[contributing](https://github.com/dalibo/temboard/blob/master/CONTRIBUTING.md)
if you\'re interested in getting involved.


# License

temBoard is available under the [PostgreSQL License].

[PostgreSQL License]: https://github.com/dalibo/temboard/blob/master/LICENSE

Candy Scordia drew *héron garde-bœuf* sketches.
