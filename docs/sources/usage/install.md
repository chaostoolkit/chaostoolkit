# How to Install the Chaos Toolkit

You can either install the chaostoolkit command line or run it directly as a
container. The former expects [Python 3.5+][python] properly
setup on your machine while the latter expects a tool implementing the
[OCI 1.0 specification][oci], such as [Docker][] or [runc][].

[python]: https://www.python.org/
[oci]: https://www.opencontainers.org/
[runc]: https://github.com/opencontainers/runc

### Python Requirements

`chaostoolkit` is implemented in Python 3 and this require a working Python
installation to run. It officially supports Python 3.5+ but may work with
other versions of the language. It has only been tested against CPython.

#### Install Python

Install Python for your system:

On MacOSX:

```
$ brew install python3
```

On Debian/Ubuntu:

```
$ sudo apt-get install python3 python3-venv
```

On CentOS:

```
$ sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
$ sudo yum -y install python35
```

On Windows:

[Download the latest binary installer][pywin] from the Python website.

[pywin]: https://www.python.org/downloads/windows/

#### Create a virtual environment

Dependencies can be installed for your system via its package management but,
more likely, you will want to install them yourself in a local virtual
environment. Let's create first such a virtual environment:

```
$ python3 -m venv ~/.venvs/chaostk
```

Make sure to always activate your virtual environment before using it:

```
$ source  ~/.venvs/chaostk/bin/activate
```

!!! tip
    You may want to use [virtualenvwrapper][] to make this process much nicer.

[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.io/en/latest/

### Install the CLI

Install `chaostoolkit` in the virtual environment as follows:

```
(chaostk) $ pip install chaostoolkit
```

You can verify the command was installed by running:

```
(chaostk) $ chaos --version
```

!!! note "Activate your virtual environment"
    Remember to always activate your virtual environment before running the
    `chaos` command.

### Download the container image

You can run the chaostoolkit from a container rather than install it.

For instance, using [Docker][docker], you can pull the
[chaostoolkit image][dockerimage]:

[docker]: https://www.docker.com/
[dockerimage]: https://hub.docker.com/r/chaostoolkit/chaostoolkit/

```
$ docker pull chaostoolkit/chaostoolkit
```
