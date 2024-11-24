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

	"""This example demonstrates logging into LOTW for a user 'CA7LSIGN' and fetching their QSOs since 2024-10-01, and then printing them out.

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

Note that you can also use the `fetch_qsos` method to fetch all QSOs; this has a simpler optional parameter set, but takes in a datetime object for date parameters. It also defaults to fetching as much information as LOTW will return about a QSO.

.. code-block:: python

	>>> import qspylib, datetime
	>>> LOTWSession = qspylib.lotw.LOTWClient('CA7LSIGN', 'password')
	>>> qsosince_datetime = datetime.datetime(2024, 10, 1)
	>>> lotw_logbook = LOTWSession.fetch_qsos(qsorxsince=qsosince_datetime)
	>>> for contact in lotw_logbook.log:
	...     print(contact)
	...
	CALL: TE1T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 025300 QSL: Y

	CALL: TE2T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 025500 QSL: Y

	CALL: TE3T BAND: 20M MODE: FT8 DATE: 20241003 TIME: 012100 QSL: Y

	CALL: TE4T BAND: 12M MODE: FT8 DATE: 20241003 TIME: 012900 QSL: N

	CALL: TE5T BAND: 40M MODE: FT8 DATE: 20241003 TIME: 003700 QSL: N

	CALL: TE6T BAND: 20M MODE: FT8 DATE: 20241003 TIME: 004500 QSL: N

Pulling the inbox from eQSL, using .adi Property
************************************************
Pulling information from a user's eQSL inbox is relatively easy with qspylib. The `fetch_inbox` method will return a Logbook object with the inbox contents.
The .adi portion of the Logbook object will contain all adif fields received from eQSL, and you can reference any present fields as dictionary keys.
Note that the eQSL divides a logbook into an inbox, and an outbox; the inbox is the QSOs that the user has received, sent for confirmation by other users.

.. code-block:: python

	"""This example demonstrates logging into eQSL for a user 'CA7LSIGN' and fetching their inbox since 2024-01-01 00:00, and then printing them out.

	This example also demonstrates using the .adi property of the Logbook; this property contains a dictionary of the entire .adi log as received from eQSL,
	where each contact is one record. All the information received from eQSL will be present in the .adi portion of the Logbook object, unlike the .log portion.
	"""

	>>> import qspylib
	>>> eQSLSession = qspylib.eqsl.eQSLClient('CA7LSIGN', 'password')
	>>> eqsl_inbox = eQSLSession.fetch_inbox(rcvd_since='202401010000')
	>>> for contact in eqsl_inbox.adi:
	...     print(contact)
	...
	<QSO_DATE:8>20231105 <TIME_ON:4>1228 <CALL:5>TE3T <MODE:4>MFSK <APP_EQSL_AG:1>Y <BAND:3>40M <EQSL_QSLRDATE:8>20240120 <EQSL_QSL_RCVD:1>Y <GRIDSQUARE:6>EM17nt <QSL_SENT:1>Y <QSL_SENT_VIA:1>E <RST_SENT:3>+01 <SUBMODE:3>FT4 <TX_PWR:8>100.0000 <EOR>

	<QSO_DATE:8>20231105 <TIME_ON:4>1230 <CALL:4>TE5T <MODE:4>MFSK <APP_EQSL_AG:1>Y <BAND:3>40M <EQSL_QSLRDATE:8>20241015 <EQSL_QSL_RCVD:1>Y <GRIDSQUARE:6>EM12qt <QSL_SENT:1>Y <QSL_SENT_VIA:1>E <RST_SENT:3>-08 <SUBMODE:3>FT4 <EOR>

	>>>str(eqsl_inbox.adi[0])
	'<QSO_DATE:8>20231105 <TIME_ON:4>1228 <CALL:5>TE3T <MODE:4>MFSK <APP_EQSL_AG:1>Y <BAND:3>40M <EQSL_QSLRDATE:8>20240120 <EQSL_QSL_RCVD:1>Y <GRIDSQUARE:6>EM17nt <QSL_SENT:1>Y <QSL_SENT_VIA:1>E <RST_SENT:3>+01 <SUBMODE:3>FT4 <TX_PWR:8>100.0000 <EOR>\n'
	>>>str(eqsl_inbox.adi[0]['CALL'])
	'TE3T'
	>>>len(eqsl_inbox.adi)
	2

Verify a QSL with eQSL
**********************
eQSL provides for confirming that a QSL is confirmed -- if it was confirmed on eQSL. This can be done by *any* user, not just a logged in one, given they have the proper information.

.. code-block:: python

	"""This example demonstrates confirming an eQSL took place with eQSL."""

	>>> from qspylib import eqsl
	>>> confirmed, raw_result = eqsl.eQSLClient.verify_eqsl('N5UP', 'TEST', '160m', 'SSB', '01/01/2000')
	>>> confirmed
	False
	>>> raw_result
	'\r\n<HTML>\r\n<HEAD></HEAD>\r\n<BODY>\r\n\r\n\r\n\r\n  Error - Result: QSO not on file\r\n  </BODY>\r\n  </HTML>\r\n  '

In current versions of qspylib, parsing raw_result for additional information, such as authenticity guaranteed status or the error cause, is left as an exercise for the reader.

Retrieving an eQSL Graphic
**************************
eQSL provides for retrieving the graphic for the digital QSL card corresponding to a QSO. Note that they request you only do at most, six requests per minute.

.. code-block:: python

	"This example demonstrates retrieving an eQSL graphic for a given QSO and displaying it using PIL."

	>>> import qspylib
	>>> from datetime import datetime
	>>> from PIL import Image
	>>> eqsl_client = qspylib.eqsl.eQSLClient("CAL7SIGN", "notarealpassword")
	>>> inbox = eqsl_client.fetch_inbox_qsls()
	>>> str(inbox.adi[12])
	'<QSO_DATE:8>20230101 <TIME_ON:4>0730 <CALL:5>TE5T <MODE:3>FT8 <APP_EQSL_AG:1>Y <BAND:3>20M <EQSL_QSLRDATE:8>20230101 <EQSL_QSL_RCVD:1>Y <GRIDSQUARE:6>EM12em <QSL_SENT:1>Y <QSL_SENT_VIA:1>E <RST_SENT:3>+00 <EOR>\n'
	>>> qso_datetime = datetime(2023, 1, 1, 7, 30)
	>>> image_data = eqsl_client.retrieve_graphic("te5t", qso_datetime, "20m", "FT8")
	>>> image_data
	<_io.BytesIO object at 0x0000000000000000>
	>>> image = Image.open(image_data)
	>>> image
	<PIL.PngImagePlugin.PngImageFile image mode=RGB size=528x336 at 0x0000000000000000>
	>>> image.show() # this will open the actual image file, showing you the image.

Looking up a callsign on QRZ
****************************
QRZ allows an authenticated user to lookup certain information about a QRZ user. This information will be returned by qspylib as a dictionary that can be parsed, sharing a structure with the XML tree returned by QRZ.
.. code-block:: python

	"""This example demonstrates grabbing information about a callsign from QRZ's XML API."""

	>>> from qspylib import qrz
	>>> QRZXMLSession = qrz.QRZXMLClient('TE5T', 'password', agent='sample_program/0.0.1')
	>>> info = QRZXMLSession.lookup_callsign('aa7bq')
	>>> info
	{'QRZDatabase': {'@version': '1.34', '@xmlns': 'http://xmldata.qrz.com', 'Callsign': {'call': 'AA7BQ', 'aliases': 'N6UFT,AA7BQ/DL1,KJ6RK,AA7BQ/HR6', 'dxcc': '291', 'attn': 'AA7BQ', 'fname': 'FRED L', 'name': 'LLOYD', 'addr1': '24 W. Camelback Rd, STE A-488', 'addr2': 'Phoenix', 'state': 'AZ', 'zip': '85013', 'country': 'United States', 'lat': '33.509665', 'lon': '-112.074142', 'grid': 'DM33xm', 'county': 'Maricopa', 'ccode': '271', 'fips': '04013', 'land': 'United States', 'efdate': '2022-04-29', 'expdate': '2030-01-20', 'class': 'E', 'codes': 'HAI', 'qslmgr': 'via QRZ', 'email': 'aa7bq@qrz.com', 'u_views': '345756', 'bio': '12804', 'biodate': '2023-02-17 17:37:29', 'image': 'https://cdn-xml.qrz.com/q/aa7bq/fred1962.jpg', 'imageinfo': '636:800:90801', 'moddate': '2022-10-09 17:32:38', 'MSA': '6200', 'AreaCode': '602', 'TimeZone': 'Mountain', 'GMTOffset': '-7', 'DST': 'N', 'eqsl': '0', 'mqsl': '0', 'cqzone': '3', 'ituzone': '6', 'born': '1953', 'lotw': '0', 'user': 'AA7BQ', 'geoloc': 'user', 'name_fmt': 'FRED L LLOYD'}, 'Session': {'Key': 'nicetrykiddo', 'Count': '539', 'SubExp': 'Mon Sep 15 02:38:30 2025', 'GMTime': 'Sun Nov 24 04:22:11 2024', 'Remark': 'cpu: 0.018s'}}}
	>>> info['QRZDatabase']['Callsign']['TimeZone']
	'Mountain'