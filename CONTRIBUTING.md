# Development Environment Setup

You can quickly set up a dev env with virtualenv and Docker Compose.

First, create a virtualenv for Python2.7, activate it. Then install temBoard and
run it with:

``` console
$ pip install -e .
$ temboard -c temboard.dev.conf --debug
```

temBoard is now waiting for PostgreSQL. Launch services:

``` console
$ docker-compose up
```

Go to https://127.0.0.1:8888/ to access temBoard runing with your code! An agent
is already set up to manage the PostgreSQL cluster of the UI.


## CSS

temBoard UI mainly relies on `Bootstrap`. The CSS files are compiled with
`SASS`.

In case you want to contribute on the styles, first install the nodeJS dev
dependencies:

```
npm install
```

Then you can either build a dist version of the css:
```
grunt sass:dist
```

Or build a dev version which will get updated each time you make a change in
any of the .scss files:
```
grunt watch
```


# Coding style

A `.editorconfig` file is included at the root of the repository configuring
whitespace and charset handling in various programming language.
The [EditorConfig]( http://editorconfig.org/#download) site links to plugins for
various editors. See `.editorconfig` for a description of the conventions.
Please stick to this conventions.

Python syntax must conform to flake8. Our CI checks new code with flake8.


# Contribution Workflow

Fork the project, commit in a branch and open a new GithUb PR on
https://github.com/dalibo/temboard.


# Releasing

To release a new version:

- Choose the next version according to `PEP 440
  <https://www.python.org/dev/peps/pep-0440/#version-scheme>`_ .
- Update ``setup.py``, without committing.
- Generate and push commit and tag with ``make release``.
- Push Python egg to PyPI using ``make upload``.
- Update docker image with `make -C docker/ clean build push`
