# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the eQSL API.
"""
from .logbook import Logbook
import requests
from ._version import __version__

# functions that don't require authentication

def verify_eqsl(CallsignFrom: str, CallsignTo: str, QSOBand: str,
                QSOMode: str = None, QSODate: str = None, timeout: int = 15):
    """Verify a QSL with eQSL.

    Args:
        CallsignFrom (str): Callsign originating QSO (i.e. N5UP)
        CallsignTo (str): Callsign receiving QSO (i.e. TE5T)
        QSOBand (str): Band QSO took place on (i.e. 160m)
        QSOMode (str, optional): Mode QSO took place with (i.e. SSB).\
            Defaults to None.
        QSODate (str, optional): Date QSO took place (i.e. 01/31/2000).\
            Defaults to None.
        timeout (int, optional): Seconds before connection times out.\
            Defaults to 15.

    Raises:
        Exception: Exception

    Returns:
        bool, str: bool of whether the QSO was verified and a str of extra\
            information eQSL reports, such as Authenticity Guaranteed status.
    """

    url = "https://www.eqsl.cc/qslcard/VerifyQSO.cfm"
    params = {
        'CallsignFrom': CallsignFrom,
        'CallsignTo': CallsignTo,
        'QSOBand': QSOBand,
        'QSOMode': QSOMode,
        'QSODate': QSODate,
    }

    with requests.Session() as s:
        r = s.get(url, params=params, headers={'user-agent': 'pyQSP/'
                                               + __version__}, timeout=timeout)
        if r.status_code == requests.codes.ok:
            raw_result = r.text
            if 'Result - QSO on file' in raw_result:
                return True, raw_result
            elif 'Parameter missing' not in raw_result:
                return False, raw_result
            else:
                raise Exception(raw_result)
        else:
            r.raise_for_status()

def retrieve_graphic(username: str, password: str, CallsignFrom: str,
                     QSOYear: str, QSOMonth: str, QSODay: str, QSOHour: str,
                     QSOMinute: str, QSOBand: str, QSOMode: str,
                     timeout: int = 15):
    """Retrieve the graphic image for a QSO from eQSL.

    Note: 
        Not yet implemented.

    Args:
        username (str): The callsign of the recipient of the eQSL
        password (str): The password of the user's account
        CallsignFrom (str): The callsign of the sender of the eQSL
        QSOYear (str): YYYY OR YY format date of the QSO
        QSOMonth (str): MM format
        QSODay (str): DD format
        QSOHour (str): HH format (24-hour time)
        QSOMinute (str): MM format
        QSOBand (str): 20m, 80M, 70cm, etc. (case insensitive)
        QSOMode (str): Must match exactly and should be an ADIF-compatible mode
        timeout (int, optional): time to connection timeout. Defaults to 15.

    Todo:
        Implement this function.

    Raises:
        NotImplementedError: Not yet implemented.
    """
    raise NotImplementedError

def get_ag_list(timeout: int = 15):
    """Get a list of Authenticity Guaranteed members. 

    Args:
        timeout (int, optional): Seconds before connection times out. Defaults to 15.

    Returns:
        tuple, str: tuple contains a list of string callsigns, and a str header with the date the list was generated
    """

    url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberList.txt"

    with requests.Session() as s:
        r = s.get(url, headers={'user-agent': 'pyQSP/' + __version__},
                  timeout=timeout)
        if r.status_code == requests.codes.ok:
            result_list = list()
            result_list += r.text.split('\r\n')
            return set(result_list[1:-1]), str(result_list[0])
        else:
            r.raise_for_status()

def get_ag_list_dated(timeout: int = 15):
    """Get a list of Authenticity Guaranteed eQSL members with the date of\
        their last upload to eQSL.

    Args:
        timeout (int, optional): Seconds before connection times out.\
            Defaults to 15.

    Returns:
        tuple: First element is a dict with key: callsign and value: date, and\
            second is a header of when this list was generated.
    """
    url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberListDated.txt"

    with requests.Session() as s:
        r = s.get(url, headers={'user-agent': 'pyQSP/' + __version__},\
                  timeout=timeout)
        if r.status_code == requests.codes.ok:
            result_list = r.text.split('\r\n')
            loc, header = result_list[1:-1], str(result_list[0])
            dict_calls = dict()
            for pair in loc:
                call, date = pair.split(', ')
                dict_calls[call] = date
            return dict_calls, header
        else:
            r.raise_for_status()

def get_full_member_list(timeout: int = 15):
    """Get a list of all members of QRZ.

    Args:
        timeout (int, optional): Seconds before connection times out.\
            Defaults to 15.

    Returns:
        dict: key is the callsign and the value is a tuple of: GridSquare, AG,\
            Last Upload
    """
    

    url = "https://www.eqsl.cc/DownloadedFiles/eQSLMemberList.csv"

    with requests.Session() as s:
        r = requests.get(url, timeout=timeout)
        if r.status_code == requests.codes.ok:
            result_list = r.text.split('\r\n')[1:-1]
            dict_calls = dict()
            for row in result_list:
                data = row.split(',')
                dict_calls[data[0]] = data[1:]
            return dict_calls
        else:
            r.raise_for_status()

def get_users_data(callsign: str, timeout: int = 15):
    """Get a specific user's data from the full member list.

    Note:
        This is incredibly slow. A better method probably involves doing some\
            vectorization, but that would require adding a dependency.

    Args:
        callsign (str): callsign to get data about
        timeout (int, optional): Seconds before connection times out.\
            Defaults to 15.

    Returns:
        tuple: contains: GridSquare, AG, Last Upload
    """
    dict_users: dict = get_full_member_list()
    return dict_users.get(callsign)


# things that require authentication
class eQSLClient:
    """API wrapper for eQSL.cc. This class holds a user's authentication to\
        perform actions on their behalf.
    """

    def __init__(self, username: str, password: str, QTHNickname: str = None,
                 timeout: int = 15):
        """Create an eQSLClient object.

        Args:
            username (str): callsign to login with
            password (str): password to login with
            QTHNickname (str, optional): QTHNickname. Defaults to None.
            timeout (int, optional): time to timeout for the entire Client.\
                Defaults to 15.
        """
        self.callsign = username,
        self.timeout = timeout
        self.base_url = "https://www.eqsl.cc/qslcard/"

        session = requests.Session()

        session.params = {k: v for k, v in {
            'username': username,
            'password': password,
            'QTHNickname': QTHNickname }.items() if v is not None}

        session.headers = {'User-Agent': 'pyQSP/' + __version__}
        self.session = session
    
    def set_timeout(self, timeout: int):
        """Set timeout for the Client to a new value.

        Args:
            timeout (int): time to timeout in seconds.
        """
        self.timeout = timeout
    
    # actual GETs

    def get_last_upload_date(self):
        """Gets last upload date for the logged in user.

        Raises:
            Exception: Exception

        Returns:
            str: date of last upload for the active user. Date is formatted:\
                DD-MMM-YYYY at HH:mm UTC
        """
        with self.session as s:
            r = s.get(self.base_url + 'DisplayLastUploadDate.cfm',
                      timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                success_txt = 'Your last ADIF upload was'
                if success_txt in r.text:
                    return r.text[r.text.index('(')+1:r.text.index(')')]
                else:
                    raise Exception(r.text)

    def fetch_inbox(self, LimitDateLo:str=None, LimitDateHi:str=None,
                    RcvdSince:str=None, ConfirmedOnly:str=None,
                    UnconfirmedOnly:str=None, Archive:str=None,
                    HamOnly:str=None):
        """Fetches INCOMING QSOs, from the user's eQSL Inbox.

        Args:
            LimitDateLo (str, optional): Earliest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F for slashes),\
                optionally append HH:MM otherwise the default is 00:00.\
                Defaults to None.
            LimitDateHi (str, optional): Latest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F), optionally\
                append HH:MM otherwise the default is 23:59 to include the\
                entire day.\
                Defaults to None.
            RcvdSince (str, optional): (YYYYMMDDHHMM) Everything that was\
                entered into the database on or after this date/time (Valid\
                range 01/01/1900 - 12/31/2078).\
                Defaults to None.
            ConfirmedOnly (str, optional): Set to any value to signify you\
                only want to download Inbox items you HAVE confirmed.\
                Defaults to None.
            UnconfirmedOnly (str, optional): Set to any value to signify you\
                only want to download Inbox items you have NOT confirmed.\
                Defaults to None.
            Archive (str, optional): 1 for Archived records ONLY; 0 for Inbox\
                (non-archived) ONLY; omit this parameter to retrieve ALL\
                records in Inbox and Archive.\
                Defaults to None.
            HamOnly (str, optional): anything, filters out all SWL contacts.\
                Defaults to None.

        Raises:
            Exception: Exception

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        params = {
            'LimitDateLo': LimitDateLo,
            'LimitDateHi': LimitDateHi,
            'RcvdSince': RcvdSince,
            'ConfirmedOnly': ConfirmedOnly,
            'UnconfirmedOnly': UnconfirmedOnly,
            'Archive': Archive,
            'HamOnly': HamOnly
        }
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}

        with self.session as s:
            r = s.get(self.base_url + "DownloadInBox.cfm", params=params,
                      timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                adif_found_txt = 'Your ADIF log file has been built'
                adif_status = r.text.index(adif_found_txt) if adif_found_txt in r.text else -1
                if adif_status < 0:
                    raise Exception('Failed to generate ADIF.')
                adif_link_start_idx = r.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = r.text.index('">.ADI file</A>')
                adif_link = self.base_url + r.text[adif_link_start_idx:adif_link_end_idx]
                adif_response = requests.get(adif_link)
                if adif_response.status_code == requests.codes.ok:
                    return Logbook(self.callsign, adif_response.text)
                else:
                    r.raise_for_status()
            else:
                r.raise_for_status()

    def fetch_outbox(self):
        """Fetches OUTGOING QSOs, from the user's eQSL Outbox.

        Raises:
            Exception: Exception
        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        with self.session as s:
            r = s.get(self.base_url + "DownloadADIF.cfm",
                      timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                adif_found_txt = 'Your ADIF log file has been built'
                adif_status = r.text.index(adif_found_txt) if adif_found_txt in r.text else -1
                if adif_status < 0:
                    raise Exception('Failed to generate ADIF.')
                adif_link_start_idx = r.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = r.text.index('">.ADI file</A>')
                adif_link = self.base_url + r.text[adif_link_start_idx:adif_link_end_idx]
                adif_response = requests.get(adif_link)
                if adif_response.status_code == requests.codes.ok   :
                    return Logbook(self.callsign, adif_response.text)
                else:
                    r.raise_for_status()
            else:
                r.raise_for_status()

    
