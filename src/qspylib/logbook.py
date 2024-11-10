# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Classes to provide the back-bone of qspylib.
"""
import adif_io

class QSO:
    """A hambaseio QSO obj. Contains simple info on a QSO.

    Attributes:
        their_call (str): callsign the QSO is with
        band (str): band of QSO
        mode (str): mode of QSO
        qso_date (str): date of QSO
        time_on (str): time start of QSO
        qsl_rcvd (str): if QSO has been confirmed
    """
    def __init__(self, their_call:str, band:str, mode:str, qso_date:str, time_on:str, qsl_rcvd:str='N'): 
        """Initializes a QSO object.

        Args:
            their_call (str): callsign the QSO is with
            band (str): band of QSO
            mode (str): mode of QSO
            qso_date (str): date of QSO
            time_on (str): time start of QSO
            qsl_rcvd (str, optional): if QSO has been confirmed. Defaults to 'N'.
        """
        self.their_call = their_call
        self.band = band
        self.mode = mode
        self.qso_date = qso_date
        self.time_on = time_on
        self.qsl_rcvd = qsl_rcvd

    def __str__(self):
        return f"CALL: {self.their_call} BAND: {self.band} MODE: {self.mode} DATE: {self.qso_date} TIME: {self.time_on} QSL: {self.qsl_rcvd}\n"
        # to-do: make this return as an actual adif formattede string

class Logbook:
    """A Logbook has both an adi field, holding all fields parsed from an .adi log per QSO, and a simplified log field, holding a simplified set of fields per QSO. A QSO is one of qspylib.logbook.QSO.
    
    Interacting with the log field can provide one field to check for if a QSO is confirmed on one or more of: LoTW, eQSL, QRZ, or ClubLog. 

    A Logbook is built by consuming an .adi formatted input string.

    Attributes:
        callsign (str): callsign of the logbook owner
        adi (dict): a dict, where each "entry" is itself a dict of fields parsed from an .adi log
        header (str): header of the .adi log
        log (set): simplified set of fields per QSO
    """

    def __init__(self, callsign: str, unparsed_log: str):
        """Initializes a Logbook.

        Args:
            callsign (str): callsign of the logbook owner
            unparsed_log (str): .adi formatted string input of a logbook
        """
        self.callsign = callsign
        self.adi, self.header = adif_io.read_from_string(unparsed_log)
        self.log = set()
        for contact in self.adi:
            # whether this qsl has been confirmed; lotw & clublog use qsl_rcvd, eqsl uses eqsl_qsl_rcvd, qrz most simply gives a qsl date
            qsl_rcvd, qrz_qsl_dte, eqsl_qsl_rcvd = contact.get('QSL_RCVD'), contact.get('app_qrzlog_qsldate'), contact.get('eqsl_qsl_rcvd')
            qso_confirmed = 'Y' if qsl_rcvd == 'Y' or qrz_qsl_dte or eqsl_qsl_rcvd == 'Y' else 'N'
            # create a QSO for this contact
            self.log.add(QSO(contact['CALL'], contact['BAND'], contact['MODE'], contact['QSO_DATE'], contact['TIME_ON'], qso_confirmed))

    def __str__(self):
        log_str = ""
        for qso in self.log:
            log_str += str(qso)
        return log_str

    def write_qso(self, contact: QSO):
        """Append a QSO to the .log portion of a Logbook.

        Note:
            This does not append to the .adi portion of a Logbook.

        Args:
            contact (QSO): QSO object to be added
        """
        self.log.add(contact)

    def discard_qso(self, contact: QSO):
        """Removes the corresponding QSO from the .log portion of a Logbook, if one exists.

        Note:
            This does not remove from the .adi portion of a Logbook.

        Args:
            contact (QSO): QSO to be deleted, if it exists
        """
        self.log.discard(contact)
        # to-do: discrad from adi?