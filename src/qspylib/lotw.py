# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import requests
from qspylib.logbook import Logbook

# exceptions

class RetrievalFailure(Exception):
    def __init__(self, message="Failed to retrieve information. Confirm log-in credentials are correct."):
        self.message=message
        super().__init__(self, message)

class UploadFailure(Exception):
    def __init__(self, message="Failed to upload file."):
        self.message=message
        super().__init__(self, message)

# functions

def get_last_upload(timeout: int = 15):
    """Queries LOTW for a list of callsigns and date they last uploaded. Returns a csv."""

    url = 'https://lotw.arrl.org/lotw-user-activity.csv'

    with requests.Session() as s:
        response = s.get(url, timeout=timeout)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()

def upload_logbook(file, timeout:int=120):
    """
    Given a .tq5 or .tq8, uploads it to LOTW. Throws an error for a connection error or if a file is rejected by LOTW, and gives the error.
    Returns the upload result message, if any.
    TO-DO: Test this actually works.
    """

    upload_url = "https://lotw.arrl.org/lotw/upload"

    data = {'upfile': file}

    with requests.Session() as s:
        response = s.post(upload_url, data, timeout=timeout)
        if response.status_code == 200:
            result = response.text
            result_start_idx = result.index('<!-- .UPL. ')
            result_end_idx = result[result_start_idx + 11:].index(' -->')
            upl_result = result[result_start_idx:result_end_idx]
            upl_message = str(result[result.index('<!-- .UPLMESSAGE. ') + 18:result[result_end_idx:].rindex(' -->')])
            if 'rejected' in upl_result:
                raise UploadFailure(upl_message)
            else:
                return upl_message
        else:
            response.raise_for_status()

class LOTWSession:
    """
    Wrapper for LOTW API functionality that requires a logged-in session.
    Fetching returns a Logbook object that must be assigned to something.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "https://lotw.arrl.org/lotwuser/"

        session = requests.Session()
        session.params = {'login': username,
                          'password': password }
        session.headers = {'User-Agent': 'pyQSP/0.0.1'}

        self.session = session

    def fetch_logbook(self, qso_query=1, qso_qsl='yes', qso_qslsince=None, qso_qsorxsince=None, qso_owncall=None, 
                      qso_callsign=None,qso_mode=None,qso_band=None,qso_dxcc=None,qso_startdate=None, qso_starttime=None, 
                      qso_enddate=None, qso_endtime=None, qso_mydetail=None,qso_qsldetail=None, qsl_withown=None):
        """
        Fetch a logbook from LOTW.

        Keyword arguments:

        qso_query --  If absent, ADIF file will contain no QSO records (default 1)
        qso_qsl --  opt, If "yes", only QSL records are returned (can be 'yes' or 'no', default 'yes')
        qso_qslsince -- opt, QSLs since specified datetime (YYYY-MM-DD HH:MM:SS). Ignored unless qso_qsl="yes".
        qso_qsorxsince -- opt, QSOs received since specified datetime. Ignored unless qso_qsl="no".
        qso_owncall -- opt, returns records where "own" call sign matches
        qso_callsign --  opt, returns records where "worked" call sign matches
        qso_mode --  opt, returns records where mode matches
        qso_band -- opt, returns records where band matches
        qso_dxcc -- opt, returns matching DXCC entities, implies qso_qsl='yes'
        qso_startdate --  opt, Returns only records with a QSO date on or after the specified value.
        qso_starttime -- opt, Returns only records with a QSO time at or after the specified value on the starting date. This value is ignored if qso_startdate is not provided.
        qso_enddate -- opt, Returns only records with a QSO date on or before the specified value.
        qso_endtime --  opt, Returns only records with a QSO time at or before the specified value on the ending date. This value is ignored if qso_enddate is not provided.
        qso_mydetail -- opt,  If "yes", returns fields that contain the Logging station's location data, if any.
        qso_qsldetail -- opt, If "yes", returns fields that contain the QSLing station's location data, if any.
        qsl_withown -- opt, If "yes", each record contains the STATION_CALLSIGN and APP_LoTW_OWNCALL fields to identify the "own" call sign used for the QSO.
        """
        log_url = "lotwreport.adi"

        params = {
            'qso_query': qso_query,
            'qso_qsl' :  qso_qsl,
            'qso_qslsince': qso_qslsince,
            'qso_qsorxsince': qso_qsorxsince,
            'qso_owncall': qso_owncall,
            'qso_callsign': qso_callsign,
            'qso_mode': qso_mode,
            'qso_band': qso_band,
            'qso_dxcc': qso_dxcc,
            'qso_startdate': qso_startdate,
            'qso_starttime': qso_starttime,
            'qso_enddate': qso_enddate,
            'qso_endtime': qso_endtime,
            'qso_mydetail': qso_mydetail,
            'qso_qsldetail': qso_qsldetail,
            'qsl_withown': qsl_withown
        }
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}

        with self.session as s:
            response = s.get(self.base_url + log_url, params=params)
            if '<eoh>' not in response.text:
                raise RetrievalFailure
            if response.status_code == 200:
                return Logbook(self.username, response.text)
            else:
                response.raise_for_status()

    def get_dxcc_credit(self, entity:str=None, ac_acct:str=None):
        """
        Gets DXCC award account credit, optionally for a specific DXCC Entity Code specified via entity.
        Note: This only returns *applied for and granted credit*, not 'presumed' credits.
        """
        dxcc_url = "logbook/qslcards.php"
        params = {
            'entity': entity,
            'ac_acct': ac_acct
        }
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}
        
        with self.session as s:
            response = s.get(self.base_url + dxcc_url, params=params)
            if response.status_code == 200:
                # lotw lies, and claims an <eoh> will be absent from bad outputs, but it's there, so we'll do something else.
                if 'ARRL Logbook of the World DXCC QSL Card Report' not in response.text[:46]:
                    raise RetrievalFailure(response.text)
                else:
                    return Logbook(self.username, response.text)
            else:
                response.raise_for_status()

