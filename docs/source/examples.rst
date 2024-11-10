Installation/Examples
=====================

Installation
*******************
All stable releases are released on PyPi and can be installed by simply running:

.. code-block:: python

    py -m pip install qspylib

This release should match what is on the GitHub repository under a corresponding tagged release.

To build the most recent source code (which isn't necessarily stable -- see the build test status), you can download the source code from GitHub, navigate to the directory, and run:

.. code-block:: python

    py -m build

This will generate a .whl and tar.gz, which you can then install locally.

Pulling a LotW Logbook and Printing QSLs since Last Login, Using .adi Property
*********************************************************************************

.. code-block:: python

	"""This example demonstrates logging into LOTW for a user 'CA7LSIGN' and fetching their QSLs with default parameters. By default, this will only return QSLs received since the last time a logbook was fetched from LOTW.
	
	This example also demonstrates using the .adi property of the Logbook; this property contains a parsed dictionary of the entire .adi log as received from LotW, and you can reference any present fields as dictionary keys.
	""" 
	
	>>> import qspylib
	>>> LOTWSession = qspylib.lotw.LOTWClient("CA7LSIGN", "password")
	>>> lotw_logbook = LOTWSession.fetch_logbook()
	>>> print(lotw_logbook) # print will print out the .log property.
	CALL: TE5T BAND: 20M MODE: SSB DATE: 20240101 TIME: 034600 QSL: Y
	>>> for contact in lotw_logbook.adi:
	...     print(contact)
	...
	<QSO_DATE:8>20240101 <TIME_ON:6>034600 <CALL:4>TE5T <FREQ:8>14.20000 <MODE:3>SSB <APP_LOTW_MODEGROUP:5>PHONE <APP_LOTW_QSO_TIMESTAMP:20>2024-01-01T03:46:00Z <APP_LOTW_RXQSL:19>2024-11-09 16:10:42 <APP_LOTW_RXQSO:19>2024-10-28 00:47:24 <BAND:3>20M <QSLRDATE:8>20241109 <QSL_RCVD:1>Y <EOR>
	>>> lotw_logbook.adi[0]["CALL"]
	'TE5T'
	>>> lotw_logbook.adi[0]["BAND"]
	'20M'
	
Pulling a LotW Logbook and Printing QSOs since Last Login, Using .log Property
*********************************************************************************

.. code-block:: python

	"""This example demonstrates logging into LOTW for a user 'CA7LSIGN' and fetching their QSOs since 2024-10-01, and then printing them out and grabbing the QSL index.
	
	This example also demonstrates using the .log property of the Logbook; this property contains a list of contacts, and each contains only very limited information about each QSO (the info as seen here.) The QSL property will "unify" the QSL fields as present in ClubLog, QRZ, LoTW, and eQSL, so it is handy for comparing confirmations between sources.
	"""
	
	>>> import qspylib
	>>> LOTWSession = qspylib.lotw.LOTWClient('CA7LSIGN', 'password')
	>>> lotw_logbook = LOTWSession.fetch_logbook(qso_qsl='no', qso_qsorxsince='2024-10-01')
	>>> for contact in lotw_logbook.log:
	...     print(contact)
	...
	CALL: TE1T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 025300 QSL: Y

	CALL: TE2T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 025500 QSL: Y

	CALL: TE3T BAND: 20M MODE: FT8 DATE: 20241003 TIME: 012100 QSL: Y

	CALL: TE4T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 012900 QSL: N

	CALL: TE5T BAND: 40M MODE: FT8 DATE: 20241003 TIME: 003700 QSL: N

	CALL: TE6T BAND: 20M MODE: FT8 DATE: 20241003 TIME: 004500 QSL: N