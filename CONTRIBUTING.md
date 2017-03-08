# Development Environment Setup

Setup quickly a development environment with Docker & Compose.

``` console
$ wget https://raw.githubusercontent.com/dalibo/docker/master/temboard/docker-compose.yml
$ docker-compose up
```

Go to https://127.0.0.0:8888/ to access temboard runing with your code!

By default, temboard is daemonized in temboardui-ui container. When editing the
code, kill first the daemonized temboard and then restart it manually.

``` console
$ docker-compose exec temboardui-ui bash
# pkill temboard
# temboard
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
    git create -b the_name_of_the_branch upstream/master
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
