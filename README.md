[![PyPI status](https://img.shields.io/pypi/status/frkl.project-meta.svg)](https://pypi.python.org/pypi/frkl.project-meta/)
[![PyPI version](https://img.shields.io/pypi/v/frkl.project-meta.svg)](https://pypi.python.org/pypi/frkl.project-meta/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/frkl.project-meta.svg)](https://pypi.python.org/pypi/frkl.project-meta/)
[![Pipeline status](https://gitlab.com/frkl/frkl.project-meta/badges/develop/pipeline.svg)](https://gitlab.com/frkl/frkl.project-meta/pipelines)
[![coverage report](https://gitlab.com/frkl/frkl.project-meta/badges/develop/coverage.svg)](https://gitlab.com/frkl/frkl.project-meta/-/commits/develop)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# frkl.project-meta

*Manage and display metadata for a project created with the frkl.python-project template.*


## Description

Documentation still to be done.


## Downloads

### Binaries

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/frkl-project)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/frkl-project.exe)
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/frkl-project)


# Development

## Requirements

- Python (version >=3.6)
- pip, virtualenv
- git
- make
- [direnv](https://direnv.net/) (optional)


## Prepare development environment

Notes:

- if using *direnv*, adjust the Python version in ``.envrc`` (should not be necessary)
- if not using *direnv*, you have to setup and activate your Python virtualenv yourself, manually, before running ``make init``

``` console
git clone https://gitlab.com/frkl/frkl.project-meta
cd frkl.project-meta
mv .envrc.disabled .envrc
direnv allow   # if using direnv, otherwise activate virtualenv
make init
```


## ``make`` targets

- ``init``: init development project (install project & dev dependencies into virtualenv, as well as pre-commit git hook)
- ``binary``: create binary for project (will install *pyenv* -- check ``scripts/build-binary`` for details)
- ``flake``: run *flake8* tests
- ``mypy``: run mypy tests
- ``test``: run unit tests
- ``docs``: create static documentation pages
- ``serve-docs``: serve documentation pages (incl. auto-reload)
- ``clean``: clean build directories

For details (and other, minor targets), check the ``Makefile``.


## Running tests

``` console
> make test
# or
> make coverage
```


## Update project template

This project uses [cruft](https://github.com/timothycrosley/cruft) to apply updates to [the base Python project template](https://gitlab.com/frkl/template-python-project) to this repository. Check out it's documentation for more information.

``` console
cruft update
# interactively approve changes, make changes if necessary
git add *
git commit -m "chore: updated project from template"
```


## Copyright & license

Please check the [LICENSE](/LICENSE) file in this repository (it's a short license!).

[Parity Public License 6.0.0](https://licensezero.com/licenses/parity)

[Copyright (c) 2020 frkl OÜ](https://frkl.io)
