# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the LotW API.
"""
from datetime import datetime
import requests
from .logbook import Logbook
from ._version import __version__

# region Exceptions


class RetrievalFailure(Exception):
    """A failure to retrieve information from LOTW. This can be due to a\
        connection error, or a bad response from the server.
    """

    def __init__(
        self,
        message="Failed to retrieve information. Confirm log-in \
                 credentials are correct.",
    ):
        self.message = message
        super().__init__(self, message)


class UploadError(Exception):
    """A failure to upload a file to LOTW. This is due to a file being\
        rejected by LOTW. The error message from LOTW is provided in the exception.
    """

    def __init__(self, message="Failed to upload file."):
        self.message = message
        super().__init__(self, message)


# endregion


# region LotW API
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
        session.params = {"login": username, "password": password}
        session.headers = {"User-Agent": "pyQSP/" + __version__}

        self.session = session

    def fetch_logbook(
        self,
        qso_query: int = 1,
        qso_qsl: str = "yes",
        qso_qslsince: str = None,
        qso_qsorxsince: str = None,
        qso_owncall: str = None,
        qso_callsign: str = None,
        qso_mode: str = None,
        qso_band: str = None,
        qso_dxcc: str = None,
        qso_startdate: str = None,
        qso_starttime: str = None,
        qso_enddate: str = None,
        qso_endtime: str = None,
        qso_mydetail: str = None,
        qso_qsldetail: str = None,
        qsl_withown: str = None,
    ) -> Logbook:
        """Fetches the user's logbook from LOTW. This function exposes *all*\
            of the parameters that can be passed to the LOTW API, including\
            ones that may be "contradictory" if used together.

        Note:
            A provided helper that uses this function may be easier to use in\
                most cases.

        Args:
            qso_query (int, optional): If absent, ADIF file will contain no\
                QSO records. Defaults to 1.
            qso_qsl (str, optional): If "yes", only QSL records are returned\
                (can be 'yes' or 'no'). Defaults to 'yes'.
            qso_qslsince (str, optional): QSLs since specified datetime\
                (YYYY-MM-DD HH:MM:SS). Ignored unless qso_qsl="yes".\
                Defaults to None.
            qso_qsorxsince (str, optional): QSOs received since specified\
                datetime. Ignored unless qso_qsl="no". Defaults to None.
            qso_owncall (str, optional): Returns records where "own" call\
                sign matches. Defaults to None.
            qso_callsign (str, optional): Returns records where "worked"\
                call sign matches. Defaults to None.
            qso_mode (str, optional): Returns records where mode matches.\
                Defaults to None.
            qso_band (str, optional): Returns records where band matches.\
                Defaults to None.
            qso_dxcc (str, optional): Returns matching DXCC entities,\
                implies qso_qsl='yes'. Defaults to None.
            qso_startdate (str, optional): Returns only records with a QSO\
                date on or after the specified value. Defaults to None.
            qso_starttime (str, optional): Returns only records with a QSO\
                time at or after the specified value on the starting date.\
                This value is ignored if qso_startdate is not provided.\
                Defaults to None.
            qso_enddate (str, optional): Returns only records with a QSO\
                date on or before the specified value. Defaults to None.
            qso_endtime (str, optional): Returns only records with a QSO\
                time at or before the specified value on the ending date.\
                This value is ignored if qso_enddate is not provided.\
                Defaults to None.
            qso_mydetail (str, optional): If "yes", returns fields that\
                contain the Logging station's location data, if any.\
                Defaults to None.
            qso_qsldetail (str, optional): If "yes", returns fields that\
                contain the QSLing station's location data, if any.\
                Defaults to None.
            qsl_withown (str, optional): If "yes", each record contains the\
                STATION_CALLSIGN and APP_LoTW_OWNCALL fields to identify the\
                "own" call sign used for the QSO. Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW.\
                Contains the error received from LOTW.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        log_url = "lotwreport.adi"

        params = {
            "qso_query": qso_query,
            "qso_qsl": qso_qsl,
            "qso_qslsince": qso_qslsince,
            "qso_qsorxsince": qso_qsorxsince,
            "qso_owncall": qso_owncall,
            "qso_callsign": qso_callsign,
            "qso_mode": qso_mode,
            "qso_band": qso_band,
            "qso_dxcc": qso_dxcc,
            "qso_startdate": qso_startdate,
            "qso_starttime": qso_starttime,
            "qso_enddate": qso_enddate,
            "qso_endtime": qso_endtime,
            "qso_mydetail": qso_mydetail,
            "qso_qsldetail": qso_qsldetail,
            "qsl_withown": qsl_withown,
        }
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}

        with self.session as s:
            response = s.get(self.base_url + log_url, params=params)
            if "<eoh>" not in response.text:
                raise RetrievalFailure
            if response.status_code == requests.codes.ok:
                return Logbook(self.username, response.text)
            raise response.raise_for_status()

    def fetch_qsls(
        self,
        qslsince: datetime = None,
        owncall: str = None,
        callsign: str = None,
        mode: str = None,
        band: str = None,
        dxcc: str = None,
        start_datetime: datetime = None,
        end_datetime: datetime = None,
    ) -> Logbook:
        """Fetches matching QSLs (confirmed QSOs) from LOTW.

        Args:
            qslsince (datetime, optional): QSLs since specified datetime\
                (YYYY-MM-DD HH:MM:SS). Defaults to None.
            owncall (str, optional):  Returns records where "own" call\
                sign matches. Defaults to None.
            callsign (str, optional): Returns records where "worked"\
                call sign matches. Defaults to None.
            mode (str, optional): Returns records where mode matches.\
                Defaults to None.
            band (str, optional): Returns records where band matches.\
                Defaults to None.
            dxcc (str, optional): Returns matching DXCC entities.\
                Defaults to None.
            start_datetime (datetime, optional): Returns only records with a QSO\
                date on or after the specified value. Optionally, includes HH:MM:SS.\
                Defaults to None.
            end_datetime (datetime, optional): Returns only records with a QSO\
                time at or before the specified value. Optionally, includes HH:MM:SS.\
                Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW.\
                Contains the error received from LOTW.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        # split datetime into date and time
        startdate, starttime = LOTWClient.__split_datetime(start_datetime)
        enddate, endtime = LOTWClient.__split_datetime(end_datetime)
        if qslsince is not None:
            if ":" in qslsince:
                qslsince = qslsince.strftime("%Y-%m-%d %H:%M:%S")
            else:
                qslsince = qslsince.strftime("%Y-%m-%d")

        return self.fetch_logbook(
            1,
            "yes",
            qso_qslsince=qslsince,
            qso_owncall=owncall,
            qso_callsign=callsign,
            qso_mode=mode,
            qso_band=band,
            qso_dxcc=dxcc,
            qso_startdate=startdate,
            qso_starttime=starttime,
            qso_enddate=enddate,
            qso_endtime=endtime,
            qso_mydetail="yes",
            qso_qsldetail="yes",
            qsl_withown="yes",
        )

    def fetch_qsos(
        self,
        qsorxsince: datetime = None,
        owncall: str = None,
        callsign: str = None,
        mode: str = None,
        band: str = None,
        dxcc: str = None,
        start_datetime: datetime = None,
        end_datetime: datetime = None,
    ) -> Logbook:
        """Fetches matching QSOs (confirmed & unconfirmed) from LOTW.

        Args:
            qsorxsince (datetime, optional): QSOs since specified datetime\
                (YYYY-MM-DD HH:MM:SS). Defaults to None.
            owncall (str, optional):  Returns records where "own" call\
                sign matches. Defaults to None.
            callsign (str, optional): Returns records where "worked"\
                call sign matches. Defaults to None.
            mode (str, optional): Returns records where mode matches.\
                Defaults to None.
            band (str, optional): Returns records where band matches.\
                Defaults to None.
            dxcc (str, optional): Returns matching DXCC entities.\
                Defaults to None.
            start_datetime (datetime, optional): Returns only records with a QSO\
                date on or after the specified value. Optionally, includes HH:MM:SS.\
                Defaults to None.
            end_datetime (datetime, optional): Returns only records with a QSO\
                time at or before the specified value. Optionally, includes HH:MM:SS.\
                Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW.\
                Contains the error received from LOTW.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        startdate, starttime = LOTWClient.__split_datetime(start_datetime)
        enddate, endtime = LOTWClient.__split_datetime(end_datetime)
        if qsorxsince is not None:
            if ":" in qsorxsince:
                qsorxsince = qsorxsince.strftime("%Y-%m-%d %H:%M:%S")
            else:
                qsorxsince = qsorxsince.strftime("%Y-%m-%d")

        return self.fetch_logbook(
            self,
            1,
            "no",
            qso_qsorxsince=qsorxsince,
            qso_owncall=owncall,
            qso_callsign=callsign,
            qso_mode=mode,
            qso_band=band,
            qso_dxcc=dxcc,
            qso_startdate=startdate,
            qso_starttime=starttime,
            qso_enddate=enddate,
            qso_endtime=endtime,
            qso_mydetail="yes",
            qso_qsldetail="yes",
            qsl_withown="yes",
        )

    def get_dxcc_credit(self, entity: str = None, ac_acct: str = None) -> Logbook:
        """Gets DXCC award account credit, optionally for a specific DXCC \
            Entity Code specified via entity.

        Note:
            This only returns *applied for and granted credit*, not 'presumed' \
                credits.

        Args:
            entity (str, optional): dxcc entity number to check for, if a \
                specific entity is desired. Defaults to None.
            ac_acct (str, optional): award account to check against, if \
                multiple exist for the given account. Defaults to None.

        Raises:
            RetrievalFailure: A failure to retrieve information from LOTW. \
                Contains the error received from LOTW.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        dxcc_url = "logbook/qslcards.php"
        params = {"entity": entity, "ac_acct": ac_acct}
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}

        with self.session as s:
            response = s.get(self.base_url + dxcc_url, params=params)
            if response.status_code == requests.codes.ok:
                # lotw lies, and claims an <eoh> will be absent from bad
                # outputs, but it's there, so we'll do something else.
                if (
                    "ARRL Logbook of the World DXCC QSL Card Report"
                    not in response.text[:46]
                ):
                    raise RetrievalFailure(response.text)
                return Logbook(self.username, response.text)
            raise response.raise_for_status()

    # region Static Functions
    @staticmethod
    def __split_datetime(dt: datetime):
        """Splits a datetime into a date and time, if a time is present.

        Args:
            dt (datetime): Datetime containing YYYY-MM-DD, and optionally, HH:MM:SS.

        Returns:
            tuple[str, str]: Tuple containing the date and time, respectively.
        """
        date, time = None, None
        date = dt.strftime("%Y-%m-%d")
        if ":" in dt:
            time = dt.strftime("%H:%M:%S")

        return date, time

    @staticmethod
    def get_last_upload(timeout: int = 15):
        """Queries LOTW for a list of callsigns and date they last uploaded.

        Args:
            timeout (int, optional): time in seconds to connection timeout.\
                Defaults to 15.

        Raises:
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            csv: a csv of callsigns and last upload date
        """

        url = "https://lotw.arrl.org/lotw-user-activity.csv"

        with requests.Session() as s:
            response = s.get(url, timeout=timeout)
            if response.status_code == requests.codes.ok:
                return response.text
            raise response.raise_for_status()

    @staticmethod
    def upload_logbook(file, timeout: int = 120):
        """Given a .tq5 or .tq8, uploads it to LOTW.

        Note:
            The "handing this a file" part of this needs to be implemented.

        Args:
            file (file): file to be uploaded
            timeout (int, optional): time in seconds to connection timeout.\
                Defaults to 120.

        Raises:
            UploadFailure: The upload was rejected by LotW.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            str: Return message from LOTW on file upload.
        """

        upload_url = "https://lotw.arrl.org/lotw/upload"

        data = {"upfile": file}

        with requests.Session() as s:
            response = s.post(upload_url, data, timeout=timeout)
            if response.status_code == requests.codes.ok:
                result = response.text
                result_start_idx = result.index("<!-- .UPL. ")
                result_end_idx = result[result_start_idx + 11 :].index(" -->")
                upl_result = result[result_start_idx:result_end_idx]
                upl_message = str(
                    result[
                        result.index("<!-- .UPLMESSAGE. ")
                        + 18 : result[result_end_idx:].rindex(" -->")
                    ]
                )
                if "rejected" in upl_result:
                    raise UploadError(upl_message)
                return upl_message
            raise response.raise_for_status()

    # endregion


# endregion
