# Installation

There are three ways to install *frkl.project-meta* on your machine. Via a manual binary download, an install script, or installation of the python package.

## Binaries

To install `frkl.project-meta`, download the appropriate binary from one of the links below, and set the downloaded file to be executable (``chmod +x project-meta``):

  - [Linux](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/linux-gnu/project-meta)
  - [Windows](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/windows/project-meta.exe)
  - [Mac OS X](https://s3-eu-west-1.amazonaws.com/dev.dl.frkl.io/darwin/project-meta)


## Install script

Alternatively, use the 'curly' install script for `frkl.project-meta`:

``` console
curl https://gitlab.com/frkl/frkl.project-meta/-/raw/develop/scripts/install/project-meta.sh | bash
```


This will add a section to your shell init file to add the install location (``$HOME/.local/share/frkl/bin``) to your ``$PATH``.

You might need to source that file (or log out and re-log in to your session) in order to be able to use *project-meta*:

``` console
source ~/.profile
```


## Python package

The python package is currently not available on [pypi](https://pypi.org), so you need to specify the ``--extra-url`` parameter for your pip command. If you chooose this install method, I assume you know how to install Python packages manually, which is why I only show you an example way of getting *frkl.project-meta* onto your machine:

``` console
> python3 -m venv ~/.venvs/frkl.project-meta
> source ~/.venvs/frkl.project-meta/bin/activate
> pip install --extra-index-url https://pkgs.frkl.io/frkl/dev --extra-index-url https://pkgs.frkl.dev/pypi frkl.project-meta
Looking in indexes: https://pypi.org/simple, https://pkgs.frkl.io/frkl/dev
Collecting frkl.project-meta
  Downloading http://pkgs.frkl.io/frkl/dev/%2Bf/ee3/f57bd91a076f9/frkl.project-meta-0.1.dev24%2Bgd3c4447-py2.py3-none-any.whl (28 kB)
...
...
...
Successfully installed aiokafka-0.6.0 aiopg-1.0.0 ... ... ...
> frkl.project-meta --help
Usage: frkl.project-meta [OPTIONS] COMMAND [ARGS]...
   ...
   ...
```
