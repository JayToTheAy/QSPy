# QSPyLib
![Python Package Build Action Status](https://github.com/JayToTheAy/QSPy/actions/workflows/python-package.yml/badge.svg)
![Documentation Status](https://readthedocs.org/projects/qspylib/badge/?version=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qspylib)
![PyPI - Version](https://img.shields.io/pypi/v/qspylib)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qspylib)
![PyPI - License](https://img.shields.io/pypi/l/qspylib)

QSPyLib is a bundle of API wrappers for various amateur radio-related sites, including QRZ, LOTW, eQSL, and ClubLog.

It is currently in development and should be considered unstable version-to-version while the version number is still 0.x.x.

Issues and pull requests are welcome, and should be made on the [GitHub repository](https://github.com/jaytotheay/qspy).

## How do I install it?

The latest stable* version of QSPyLib is available on PyPI, and can be installed by just running

```bash
py -m pip install qspylib
```

This release should match what is on the GitHub repository under a corresponding tagged release.

To build the most recent source code (which isn’t necessarily stable – see the build test status), you can download the source code from GitHub, navigate to the directory, and run:

```py
py -m build
```

This will generate a .whl and tar.gz, which you can then install locally.

## What works right now?

As of v0.0.1:

* The LotW module is, in theory, finished -- no doubt something will come up about how it's not actually practical and needs more work.
* The eQSL module has most of the functionality of eQSL's API, but is incredibly unpolished and needs more work.
* The QRZ module exists; the Logbook API is currently only supported for FETCH operations, and the XML Interface is not supported yet.
* The ClubLog module is on-hold pending the ready-status of the other modules.

## How do I use it?

Documentation of all functions and classes, including examples, is available at the ReadTheDocs listing for this project:

<http://qspylib.readthedocs.io/>

A quick example of pulling a Logbook from LOTW:

```py
from qspylib import lotw
LOTWAccount = lotw.LOTWClient("callsign", "password")
logbook = LOTWClient.fetch_logbook()
```
This will give you a `Logbook` object, which contains a list of QSO objects and a parsed, usable adif_io log.
The adif_io log property contains all the ADIF info that LOTW outputs (and likewise for other logging sites).
The built-in log property of a `Logbook` object contains only some limited information, like callsign, band, mode, date, time, and QSL status from the originating site (which is a little handy as a single-reference for if a QSO is a QSL, since different sites use different, extra ADIF fields to express being QSL'd on their platform.)

Other functions of APIs are generally available, like checking if an eQSL is verified:

```py
from qspylib import eqsl
confirmed, raw_result = eqsl.verify_eqsl('N5UP', 'TEST', '160m', 'SSB', '01/01/2000')
```
This will return a tuple; here, `confirmed` will be False, since this QSO is not verified on eQSL, and `raw_result` will contain any extra information eQSL provides, for instance, if it's Authenticity Guaranteed.

Modules, functions, and classes are documented in-code via docstrings, and you can learn more by reading those docstrings; you can also read the [Read the Docs](http://qspylib.readthedocs.io/) listings for a visually pleasing guide on what the docstrings say.
