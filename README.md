# QSPyLib
![Python Package Build Action Status](https://github.com/JayToTheAy/QSPy/actions/workflows/python-package.yml/badge.svg)
![Documentation Status](https://readthedocs.org/projects/qspylib/badge/?version=latest)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qspylib)
![PyPI - Version](https://img.shields.io/pypi/v/qspylib)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qspylib)
![PyPI - License](https://img.shields.io/pypi/l/qspylib)

QSPyLib is a bundle of API wrappers for various amateur radio-related sites, including QRZ, LOTW, eQSL, and ClubLog.

QSPyLib is in active development; that said, major version numbers should maintain API stability. If you need absolute stability of the API, fix your version against the major.

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

As of v1.0.0:

* The LotW module is, in theory, finished -- you can download QSOs in bulk or by criteria, check DXCC credit, get a list of users and their date of last upload, and upload a log.
* The eQSL module has most of the functionality of eQSL's API, but is a bit unpolished -- at present, you can fetch inboxes and outboxes, get AG lists, get member lists, get last upload data for users, verify an eQSL, and retrieve the eQSL card graphic for a QSL.
* The QRZ module is done; for logs, we support fetching logbooks, checking logbook statuses, and inserting and deleting records. For the XML API, we support looking up a callsign's data and looking up a DXCC's data.
* The ClubLog module only supports grabbing logbooks from ClubLog at the moment.

Everything has been tested to work when done "correctly" and simply; no doubt some edge case will pop up, or some failure state won't throw a good error. Please open an issue for *any* problems you come across, no matter how minor, even if it's just an exception that isn't descriptive.

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
confirmed, raw_result = eqsl.eQSLClient.verify_eqsl('N5UP', 'TEST', '160m', 'SSB', '01/01/2000')
```
This will return a tuple; here, `confirmed` will be False, since this QSO is not verified on eQSL, and `raw_result` will contain any extra information eQSL provides, for instance, if it's Authenticity Guaranteed. Note that verify_eqsl is a static method of the eQSLClient class, and can be called either from an eQSLClient object, or directly from the class.

Modules, functions, and classes are documented in-code via docstrings, and you can learn more by reading those docstrings; you can also read the [Read the Docs](http://qspylib.readthedocs.io/) listings for a visually pleasing guide on what the docstrings say.
