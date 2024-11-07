# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from qspylib.logbook import Logbook
import requests
from qspylib._version import __version__

# functions that don't require authentication

def verify_eqsl(CallsignFrom: str, CallsignTo: str, QSOBand: str, QSOMode: str = None, QSODate: str = None, timeout: int = 15):
    """
    Verify a QSL with eQSL. Returns a tuple containing a Boolean of whether the QSO was verified, and the result str with any extra information.

    Keyword arguments:

    CallsignFrom -- Callsign originating QSO (i.e. N5UP)
    CallsignTo -- Callsign receiving QSO (i.e. TEST)
    QSOBand -- Band QSO took place on (i.e. 160m)
    QSOMode -- Mode QSO took place with (i.e. SSB)
    QSODate -- Date QSO took place (i.e. 01/31/2000)
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
        r = s.get(url, params=params, headers={'user-agent': 'pyQSP/' + __version__}, timeout=timeout)
        if r.status_code == 200:
            raw_result = r.text
            if 'Result - QSO on file' in raw_result:
                return True, raw_result
            elif 'Parameter missing' not in raw_result:
                return False, raw_result
            else:
                raise Exception(raw_result)
        else:
            r.raise_for_status()

def retrieve_graphic():
    raise NotImplementedError

def get_ag_list(timeout: int = 15):
    """Get a list of Authenticity Guaranteed members. Tuple contains a list of string callsigns, and a string header with the date the list was generated."""

    url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberList.txt"

    with requests.Session() as s:
        r = s.get(url, headers={'user-agent': 'pyQSP/' + __version__}, timeout=timeout)
        if r.status_code == 200:
            result_list = list()
            result_list += r.text.split('\r\n')
            return set(result_list[1:-1]), str(result_list[0])
        else:
            r.raise_for_status()

def get_ag_list_dated(timeout: int = 15):
    """
    Get a list of Authenticity Guaranteed eQSL members with the date of their last upload to eQSL.
    Returns a tuple. First element is a dict with key: callsign and value: date, and second is a header of when this list was generated.
    """
    url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberListDated.txt"

    with requests.Session() as s:
        r = s.get(url, headers={'user-agent': 'pyQSP/' + __version__}, timeout=timeout)
        if r.status_code == 200:
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
    """Get a list of all members of QRZ. Returns a dict, where the key is the callsign and the value is a tuple of: GridSquare, AG, Last Upload"""

    url = "https://www.eqsl.cc/DownloadedFiles/eQSLMemberList.csv"

    with requests.Session() as s:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            result_list = r.text.split('\r\n')[1:-1]
            dict_calls = dict()
            for row in result_list:
                data = row.split(',')
                dict_calls[data[0]] = data[1:]
            return dict_calls
        else:
            r.raise_for_status()

def get_users_data(callsign: str, timeout: int = 15):
    """
    Returns a dict of data on a QRZ user, in the form of: GridSquare, AG, Last Upload
    Note: Slow. Would be faster with vectorization, but then we'd need dependencies.
    """
    dict_users: dict = get_full_member_list()
    return dict_users.get(callsign)


# things that require authentication
class eQSLSession:
    """
    API wrapper for eQSL. At present, only handles fetching inbox QSOs.
    Fetching returns a Logbook object that must be assigned to something.
    """

    def __init__(self, username: str, password: str, QTHNickname: str = None, timeout: int = 15):
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
        self.timeout = timeout
    
    # actual GETs

    def get_last_upload_date(self):
        " Returns a string with the date of last upload for the active user. Date is formatted: DD-MMM-YYYY at HH:mm UTC"

        with self.session as s:
            r = s.get(self.base_url + 'DisplayLastUploadDate.cfm', timeout=self.timeout)
            if r.status_code == 200:
                success_txt = 'Your last ADIF upload was'
                if success_txt in r.text:
                    return r.text[r.text.index('(')+1:r.text.index(')')]
                else:
                    raise Exception(r.text)

    def fetch_inbox(self, LimitDateLo=None, LimitDateHi=None, RcvdSince=None, ConfirmedOnly=None, UnconfirmedOnly=None, Archive=None, HamOnly=None):
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
            r = s.get(self.base_url + "DownloadInBox.cfm", params=params, timeout=self.timeout)
            if r.status_code == 200:
                adif_found_txt = 'Your ADIF log file has been built'
                adif_status = r.text.index(adif_found_txt) if adif_found_txt in r.text else -1
                if adif_status < 0:
                    raise Exception('Failed to generate ADIF.')
                adif_link_start_idx = r.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = r.text.index('">.ADI file</A>')
                adif_link = self.base_url + r.text[adif_link_start_idx:adif_link_end_idx]
                adif_response = requests.get(adif_link)
                if adif_response.status_code == 200:
                    return Logbook(self.callsign, adif_response.text)
                else:
                    r.raise_for_status()
            else:
                r.raise_for_status()

    def fetch_outbox(self):
        # TO-DO: test
        with self.session as s:
            r = s.get(self.base_url + "DownloadADIF.cfm", timeout=self.timeout)
            if r.status_code == 200:
                adif_found_txt = 'Your ADIF log file has been built'
                adif_status = r.text.index(adif_found_txt) if adif_found_txt in r.text else -1
                if adif_status < 0:
                    raise Exception('Failed to generate ADIF.')
                adif_link_start_idx = r.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = r.text.index('">.ADI file</A>')
                adif_link = self.base_url + r.text[adif_link_start_idx:adif_link_end_idx]
                adif_response = requests.get(adif_link)
                if adif_response.status_code == 200:
                    return Logbook(self.callsign, adif_response.text)
                else:
                    r.raise_for_status()
            else:
                r.raise_for_status()

    
