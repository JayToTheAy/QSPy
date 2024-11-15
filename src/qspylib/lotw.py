# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the LotW API.
"""
import requests
from .logbook import Logbook
from ._version import __version__

# exceptions

class RetrievalFailure(Exception):
    """A failure to retrieve information from LOTW. This can be due to a connection error, or a bad response from the server.
    """
    def __init__(self, message="Failed to retrieve information. Confirm log-in credentials are correct."):
        self.message=message
        super().__init__(self, message)

class UploadFailure(Exception):
    """A failure to upload a file to LOTW. This is due to a file being rejected by LOTW. The error message from LOTW is provided in the exception.
    """
    def __init__(self, message="Failed to upload file."):
        self.message=message
        super().__init__(self, message)

# functions

def get_last_upload(timeout: int = 15):
    """Queries LOTW for a list of callsigns and date they last uploaded.

    Args:
        timeout (int, optional): time in seconds to connection timeout. Defaults to 15.

    Returns:
        csv: a csv of callsigns and last upload date
    """

    url = 'https://lotw.arrl.org/lotw-user-activity.csv'

    with requests.Session() as s:
        response = s.get(url, timeout=timeout)
        if response.status_code == requests.codes.ok:
            return response.text
        else:
            response.raise_for_status()

def upload_logbook(file, timeout:int=120):
    """Given a .tq5 or .tq8, uploads it to LOTW.

    Note:
        The "handing this a file" part of this needs to be implemented.

    Args:
        file (_type_): file to be uploaded
        timeout (int, optional): time in seconds to connection timeout. Defaults to 120.

    Raises:
        UploadFailure: Why the upload failed.

    Returns:
        str: Return message from LOTW on file upload.
    """

    upload_url = "https://lotw.arrl.org/lotw/upload"

    data = {'upfile': file}

    with requests.Session() as s:
        response = s.post(upload_url, data, timeout=timeout)
        if response.status_code == requests.codes.ok:
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

class LOTWClient:
    """Wrapper for LOTW API functionality that requires a logged-in session.
    Fetching returns a Logbook object that must be assigned to something._
    """

    def __init__(self, username: str, password: str):
        """Initialize a LOTWClient object.

        Args:
            username (str): username (callsign) for LOTW
            password (str): password
        """
        self.username = username
        self.password = password
        self.base_url = "https://lotw.arrl.org/lotwuser/"

        session = requests.Session()
        session.params = {'login': username,
                          'password': password }
        session.headers = {'User-Agent': 'pyQSP/' + __version__}

        self.session = session

    def fetch_logbook(self, qso_query=1, qso_qsl='yes', qso_qslsince=None, qso_qsorxsince=None, qso_owncall=None, 
                      qso_callsign=None,qso_mode=None,qso_band=None,qso_dxcc=None,qso_startdate=None, qso_starttime=None, 
                      qso_enddate=None, qso_endtime=None, qso_mydetail=None,qso_qsldetail=None, qsl_withown=None):
        """_summary_

        Args:
            qso_query (int, optional): If absent, ADIF file will contain no QSO records. Defaults to 1.
            qso_qsl (str, optional): If "yes", only QSL records are returned (can be 'yes' or 'no'). Defaults to 'yes'.
            qso_qslsince (_type_, optional): QSLs since specified datetime (YYYY-MM-DD HH:MM:SS). Ignored unless qso_qsl="yes". Defaults to None.
            qso_qsorxsince (_type_, optional): QSOs received since specified datetime. Ignored unless qso_qsl="no". Defaults to None.
            qso_owncall (_type_, optional): Returns records where "own" call sign matches. Defaults to None.
            qso_callsign (_type_, optional): Returns records where "worked" call sign matches. Defaults to None.
            qso_mode (_type_, optional): Returns records where mode matches. Defaults to None.
            qso_band (_type_, optional): Returns records where band matches. Defaults to None.
            qso_dxcc (_type_, optional): Returns matching DXCC entities, implies qso_qsl='yes'. Defaults to None.
            qso_startdate (_type_, optional): Returns only records with a QSO date on or after the specified value. Defaults to None.
            qso_starttime (_type_, optional): Returns only records with a QSO time at or after the specified value on the starting date. This value is ignored if qso_startdate is not provided. Defaults to None.
            qso_enddate (_type_, optional): Returns only records with a QSO date on or before the specified value. Defaults to None.
            qso_endtime (_type_, optional): Returns only records with a QSO time at or before the specified value on the ending date. This value is ignored if qso_enddate is not provided. Defaults to None.
            qso_mydetail (_type_, optional): If "yes", returns fields that contain the Logging station's location data, if any. Defaults to None.
            qso_qsldetail (_type_, optional): If "yes", returns fields that contain the QSLing station's location data, if any. Defaults to None.
            qsl_withown (_type_, optional): If "yes", each record contains the STATION_CALLSIGN and APP_LoTW_OWNCALL fields to identify the "own" call sign used for the QSO. Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW. Contains the error received from LOTW.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
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
            if response.status_code == requests.codes.ok:
                return Logbook(self.username, response.text)
            else:
                response.raise_for_status()

    def get_dxcc_credit(self, entity:str=None, ac_acct:str=None):
        """Gets DXCC award account credit, optionally for a specific DXCC Entity Code specified via entity.

        Note:
            This only returns *applied for and granted credit*, not 'presumed' credits.

        Args:
            entity (str, optional): dxcc entity number to check for, if a specific entity is desired. Defaults to None.
            ac_acct (str, optional): award account to check against, if multiple exist for the given account. Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW. Contains the error received from LOTW.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
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
            if response.status_code == requests.codes.ok:
                # lotw lies, and claims an <eoh> will be absent from bad outputs, but it's there, so we'll do something else.
                if 'ARRL Logbook of the World DXCC QSL Card Report' not in response.text[:46]:
                    raise RetrievalFailure(response.text)
                else:
                    return Logbook(self.username, response.text)
            else:
                response.raise_for_status()

