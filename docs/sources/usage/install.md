## Install chaostoolkit

### Requirements

`chaostoolkit` is implemented in Python 3 and this require a working Python
installation to run. It officially supports Python 3.5+ but may work with
other versions of the language. It has only been tested against CPython.

Install Python as per your system, then, install the dependencies for 
`chaostoolkit`.

These can either be installed for your system via its package management but,
more likely, you will want to install them from sources using [pip][]. `pip`
should be present in your Python distribution. Alternatively you can install
`pip` from its [sources][pip-install].

[pip]: https://pip.pypa.io/en/stable/
[pip-install]: https://pip.pypa.io/en/stable/installing/

Once Python and `pip` are present on your system, create a 
[virtual environment][venv] to install the `chaostoolkit` dependencies into.

[venv]: https://virtualenv.pypa.io/en/stable/

Now that you have a virtual environment, make sure it is enabled and install
the dependencies:

```
(venv) $ pip install -r requirements.txt
```

### Install the CLI

Once your dependencies are deployed properly, install `chaostoolkit` in the
virtual environment:

```
(venv) $ pip install chaostoolkit
```

You can verify the command was installed by running:

```
(venv) $ chaos --version
```
