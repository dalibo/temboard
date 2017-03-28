# Development Environment Setup

You can quickly set up a dev env with virtualenv and Docker Compose.

First, create a virtualenv, activate it, install temboard and run it:

``` console
$ pip install -e .
$ temboard -c temboard.dev.conf --debug
```

Temboard is now waiting for postgres. Now launch services:

``` console
$ docker-compose up
```

Go to https://127.0.0.1:8888/ to access temboard runing with your code!

## CSS

Temboard UI mainly relies on `Bootstrap`. The CSS files are compiled with
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

# GitHub Workflow

Here is our prefered way to manage the git/github workflow.

These are recommendations only.

## Fork the Project

Go to github's [project main page](https://github.com/dalibo/temboard). Then click on the `Fork` button to create a copy of the project in your github account.

Then clone the project on own computer:

```
    git clone git@github.com:your_username/temboard.git
```

This will create a remote repository called `origin`.

Add a remote configuration for the official repo.

```
    git remote add upstream https://github.com/dalibo/temboard.git
```

This will help making sure you are working on the very last version of the code. See the "Create a branch" section below.

You're now ready to fix a bug or add new stuff.

## Fix a Bug / Develop New Features


The following command will fetch the newest changes in the official repo.

```
    git remote update
```

Then you can **create a new branch**.

```
    git checkout -b the_name_of_the_branch upstream/master
```

Change/Add some code, commit your stuff. Then, push your changes to github:

```
    git push origin the_name_of_the_branch
```

Create a pull request. See below.

Don't forget to create a new branch each time you want to work on something different.

## Create a Pull Request

Please follow the instructions as proposed in [pull request documentation](https://help.github.com/articles/using-pull-requests) on github.

Don't forget to give as much details as possible.

Project maintainers will hopefully review your code and give you some feedback.

### Configure your editor

If possible, configure your editor to follow the coding conventions of the
library.  A `.editorconfig` file is included at the root of the repository that
can be used to configure whitespace and charset handling in your editor.  See
that file for a description of the conventions.  The [EditorConfig](
http://editorconfig.org/#download) site links to plugins for various editors.
