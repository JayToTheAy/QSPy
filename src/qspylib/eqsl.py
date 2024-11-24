# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the eQSL API.
"""
from datetime import datetime
from io import BytesIO
import requests
from .logbook import Logbook
from ._version import __version__


# region Exceptions
class eQSLError(Exception):  # pylint: disable=invalid-name
    """An error occurred interfacing with eQSL."""

    def __init__(self, message="An error occurred interfacing with eQSL"):
        super().__init__(message)


# endregion


# region eQSL API Wrapper
class eQSLClient:  # pylint: disable=invalid-name
    """API wrapper for eQSL.cc. This class holds a user's authentication to\
        perform actions on their behalf.
    """

    def __init__(
        self, username: str, password: str, qth_nickname: str = None, timeout: int = 15
    ):
        """Create an eQSLClient object.

        Args:
            username (str): callsign to login with
            password (str): password to login with
            qth_nickname (str, optional): QTHNickname. Defaults to None.
            timeout (int, optional): time to timeout for the entire Client.\
                Defaults to 15.
        """
        self.callsign = username
        self.timeout = timeout
        self.base_url = "https://www.eqsl.cc/qslcard/"

        session = requests.Session()

        session.params = {
            k: v
            for k, v in {
                "username": username,
                "password": password,
                "QTHNickname": qth_nickname,
            }.items()
            if v is not None
        }

        session.headers = {"User-Agent": "pyQSP/" + __version__}
        self.session = session

    def set_timeout(self, timeout: int):
        """Set timeout for the Client to a new value.

        Args:
            timeout (int): time to timeout in seconds.
        """
        self.timeout = timeout

    # actual GETs

    def get_last_upload_date(self) -> datetime:
        """Gets last upload date for the logged in user.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            datetime.datetime: datetime of last upload for the active user.\
                Contains: Year, Month, Date, Hour, Minute (UTC).
        """
        with self.session as s:
            response = s.get(
                self.base_url + "DisplayLastUploadDate.cfm", timeout=self.timeout
            )
            if response.status_code == requests.codes.ok:
                success_txt = "Your last ADIF upload was"
                if success_txt in response.text:
                    time_str = response.text[
                        response.text.index("(") + 1 : response.text.index(")")
                    ]
                    return datetime.strptime(time_str, "%d-%b-%Y at %H:%M UTC")
                raise eQSLError(response.text)
            raise response.raise_for_status()

    def fetch_inbox(
        self,
        limit_date_lo: str = None,
        limit_date_hi: str = None,
        rcvd_since: str = None,
        confirmed_only: str = None,
        unconfirmed_only: str = None,
        archive: str = None,
        ham_only: str = None,
    ) -> Logbook:
        """Fetches INCOMING QSOs, from the user's eQSL Inbox.

        Args:
            limit_date_lo (str, optional): Earliest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F for slashes),\
                optionally append HH:MM otherwise the default is 00:00.\
                Defaults to None.
            limit_date_hi (str, optional): Latest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F), optionally\
                append HH:MM otherwise the default is 23:59 to include the\
                entire day.\
                Defaults to None.
            rcvd_since (str, optional): (YYYYMMDDHHMM) Everything that was\
                entered into the database on or after this date/time (Valid\
                range 01/01/1900 - 12/31/2078).\
                Defaults to None.
            confirmed_only (str, optional): Set to any value to signify you\
                only want to download Inbox items you HAVE confirmed.\
                Defaults to None.
            unconfirmed_only (str, optional): Set to any value to signify you\
                only want to download Inbox items you have NOT confirmed.\
                Defaults to None.
            archive (str, optional): 1 for Archived records ONLY; 0 for Inbox\
                (non-archived) ONLY; omit this parameter to retrieve ALL\
                records in Inbox and Archive.\
                Defaults to None.
            ham_only (str, optional): anything, filters out all SWL contacts.\
                Defaults to None.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        params = {
            "LimitDateLo": limit_date_lo,
            "LimitDateHi": limit_date_hi,
            "RcvdSince": rcvd_since,
            "ConfirmedOnly": confirmed_only,
            "UnconfirmedOnly": unconfirmed_only,
            "Archive": archive,
            "HamOnly": ham_only,
        }
        # filter down to only used params
        params = {k: v for k, v in params.items() if v is not None}

        with self.session as s:
            response = s.get(
                self.base_url + "DownloadInBox.cfm", params=params, timeout=self.timeout
            )
            if response.status_code == requests.codes.ok:
                adif_found_txt = "Your ADIF log file has been built"
                adif_status = (
                    response.text.index(adif_found_txt)
                    if adif_found_txt in response.text
                    else -1
                )
                if adif_status < 0:
                    raise eQSLError("Failed to generate ADIF.")
                adif_link_start_idx = response.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = response.text.index('">.ADI file</A>')
                adif_link = (
                    self.base_url + response.text[adif_link_start_idx:adif_link_end_idx]
                )
                adif_response = requests.get(adif_link, timeout=self.timeout)
                if adif_response.status_code == requests.codes.ok:
                    return Logbook(self.callsign, adif_response.text)
                raise response.raise_for_status()
            raise response.raise_for_status()

    def fetch_inbox_qsls(
        self,
        limit_date_lo: str = None,
        limit_date_hi: str = None,
        rcvd_since: str = None,
        archive: str = None,
        ham_only: str = None,
    ) -> Logbook:
        """Fetches INCOMING QSLs, from the user's eQSL Inbox.

        limit_date_lo (str, optional): Earliest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F for slashes),\
                optionally append HH:MM otherwise the default is 00:00.\
                Defaults to None.
            limit_date_hi (str, optional): Latest QSO date to download\
                (oddly, in MM/DD/YYYY format with escape code 2F), optionally\
                append HH:MM otherwise the default is 23:59 to include the\
                entire day.\
                Defaults to None.
            rcvd_since (str, optional): (YYYYMMDDHHMM) Everything that was\
                entered into the database on or after this date/time (Valid\
                range 01/01/1900 - 12/31/2078).\
                Defaults to None.
            archive (str, optional): 1 for Archived records ONLY; 0 for Inbox\
                (non-archived) ONLY; omit this parameter to retrieve ALL\
                records in Inbox and Archive.\
                Defaults to None.
            ham_only (str, optional): anything, filters out all SWL contacts.\
                Defaults to None.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        return self.fetch_inbox(
            limit_date_lo, limit_date_hi, rcvd_since, "Y", None, archive, ham_only
        )

    def fetch_outbox(self):
        """Fetches OUTGOING QSOs, from the user's eQSL Outbox.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        with self.session as s:
            response = s.get(self.base_url + "DownloadADIF.cfm", timeout=self.timeout)
            if response.status_code == requests.codes.ok:
                adif_found_txt = "Your ADIF log file has been built"
                adif_status = (
                    response.text.index(adif_found_txt)
                    if adif_found_txt in response.text
                    else -1
                )
                if adif_status < 0:
                    raise eQSLError("Failed to generate ADIF.")
                adif_link_start_idx = response.text.index('<LI><A HREF="..') + 15
                adif_link_end_idx = response.text.index('">.ADI file</A>')
                adif_link = (
                    self.base_url + response.text[adif_link_start_idx:adif_link_end_idx]
                )
                adif_response = requests.get(adif_link, timeout=self.timeout)
                if adif_response.status_code == requests.codes.ok:
                    return Logbook(self.callsign, adif_response.text)
                raise response.raise_for_status()
            raise response.raise_for_status()

    def _retrieve_graphic(
        self,
        callsign_from: str,
        qso_year: str,
        qso_month: str,
        qso_day: str,
        qso_hour: str,
        qso_minute: str,
        qso_band: str,
        qso_mode: str,
        timeout: int = 15,
    ) -> BytesIO:
        """Retrieve the graphic image for a QSO from eQSL. This is the raw\
        interface, as provided by eQSL.cc, with string parameters.

        Note:
            It is recommended you use the `retrieve_graphic` method instead.

        Args:
            callsign_from (str): The callsign of the sender of the eQSL
            qso_year (str): YYYY OR YY format date of the QSO
            qso_month (str): MM format
            qso_day (str): DD format
            qso_hour (str): HH format (24-hour time)
            qso_minute (str): MM format
            qso_band (str): 20m, 80M, 70cm, etc. (case insensitive)
            qso_mode (str): Must match exactly and should be an ADIF-compatible mode
            timeout (int, optional): time to connection timeout. Defaults to 15.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            BytesIO: A BytesIO binary stream containing the image data. This\
                can be further processed with PIL or other image libraries;\
                for instance, using PIL, Image.open(return_val) will give a PIL Image.
        """
        params = {
            "CallsignFrom": callsign_from,
            "QSOYear": qso_year,
            "QSOMonth": qso_month,
            "QSODay": qso_day,
            "QSOHour": qso_hour,
            "QSOMinute": qso_minute,
            "QSOBand": qso_band,
            "QSOMode": qso_mode,
        }
        response = self.session.get(
            self.base_url + "GeteQSL.cfm", params=params, timeout=timeout
        )
        if response.status_code == requests.codes.ok:
            try:
                url_beg_idx = response.text.index('<img src="') + 10
                url_end_idx = response.text.index('" alt="')
                img_url = "https://www.eQSL.cc" + response.text[url_beg_idx:url_end_idx]
                img_response = self.session.get(img_url, stream=True, timeout=timeout)
                return BytesIO(img_response.content)
            except ValueError as exc:
                raise eQSLError("Failed to retrieve graphic image") from exc
        else:
            raise response.raise_for_status()

    def retrieve_graphic(
        self,
        callsign_from: str,
        qso_datetime: datetime,
        band: str,
        mode: str,
        timeout: int = 15,
    ) -> BytesIO:
        """Retrieve the graphic image for a QSO from eQSL. This is a simplified\
        interface that uses a datetime object.

        Args:
            callsign_from (str): The callsign of the sender of the eQSL
            qso_datetime (datetime): Datetime containing the Year, Month, Day,\
                Hour, and Minute of the QSO.
            band (str): 20m, 80M, 70cm, etc. (case insensitive)
            mode (str): Must match exactly and should be an ADIF-compatible mode
            timeout (int, optional): Seconds before query times out. Defaults to 15.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            BytesIO: A BytesIO binary stream containing the image data. This\
                can be further processed with PIL or other image libraries;\
                for instance, using PIL, Image.open(return_val) will give a PIL Image.
        """
        return self._retrieve_graphic(
            callsign_from,
            qso_datetime.year,
            qso_datetime.month,
            qso_datetime.day,
            qso_datetime.hour,
            qso_datetime.minute,
            band,
            mode,
            timeout,
        )

    # region Static Methods

    @staticmethod
    def verify_eqsl(
        callsign_from: str,
        callsign_to: str,
        qso_band: str,
        qso_mode: str = None,
        qso_date: str = None,
        timeout: int = 15,
    ):
        """Verify a QSL with eQSL.

        Args:
            callsign_from (str): Callsign originating QSO (i.e. N5UP)
            callsign_to (str): Callsign receiving QSO (i.e. TE5T)
            qso_band (str): Band QSO took place on (i.e. 160m)
            qso_mode (str, optional): Mode QSO took place with (i.e. SSB).\
                Defaults to None.
            qso_date (str, optional): Date QSO took place (i.e. 01/31/2000).\
                Defaults to None.
            timeout (int, optional): Seconds before connection times out.\
                Defaults to 15.

        Raises:
            eQSLError: An error occurred interfacing with eQSL.
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            bool, str: bool of whether the QSO was verified and a str of extra\
                information eQSL reports, such as Authenticity Guaranteed status.
        """

        url = "https://www.eqsl.cc/qslcard/VerifyQSO.cfm"
        params = {
            "CallsignFrom": callsign_from,
            "CallsignTo": callsign_to,
            "QSOBand": qso_band,
            "QSOMode": qso_mode,
            "QSODate": qso_date,
        }

        with requests.Session() as s:
            response = s.get(
                url,
                params=params,
                headers={"user-agent": "pyQSP/" + __version__},
                timeout=timeout,
            )
            if response.status_code == requests.codes.ok:
                raw_result = response.text

                if "Result - QSO on file" in raw_result:
                    return True, raw_result
                if "Parameter missing" not in raw_result:
                    return False, raw_result
                raise eQSLError(raw_result)
            raise response.raise_for_status()

    @staticmethod
    def get_ag_list(timeout: int = 15):
        """Get a list of Authenticity Guaranteed members.

        Args:
            timeout (int, optional): Seconds before connection times out. Defaults to 15.

        Raises:
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            tuple, str: tuple contains a list of string callsigns, and a str header\
                with the date the list was generated
        """

        url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberList.txt"

        with requests.Session() as s:
            response = s.get(
                url, headers={"user-agent": "pyQSP/" + __version__}, timeout=timeout
            )
            if response.status_code == requests.codes.ok:
                result_list = []
                result_list += response.text.split("\r\n")
                return set(result_list[1:-1]), str(result_list[0])
            raise response.raise_for_status()

    @staticmethod
    def get_ag_list_dated(timeout: int = 15):
        """Get a list of Authenticity Guaranteed eQSL members with the date of\
            their last upload to eQSL.

        Args:
            timeout (int, optional): Seconds before connection times out.\
                Defaults to 15.

        Raises:
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            tuple: First element is a dict with key: callsign and value: date, and\
                second is a header of when this list was generated.
        """
        url = "https://www.eqsl.cc/qslcard/DownloadedFiles/AGMemberListDated.txt"

        with requests.Session() as s:
            response = s.get(
                url, headers={"user-agent": "pyQSP/" + __version__}, timeout=timeout
            )
            if response.status_code == requests.codes.ok:
                result_list = response.text.split("\r\n")
                loc, header = result_list[1:-1], str(result_list[0])
                dict_calls = {}
                for pair in loc:
                    call, date = pair.split(", ")
                    dict_calls[call] = date
                return dict_calls, header
            raise response.raise_for_status()

    @staticmethod
    def get_full_member_list(timeout: int = 15):
        """Get a list of all members of QRZ.

        Args:
            timeout (int, optional): Seconds before connection times out.\
                Defaults to 15.

        Raises:
            HTTPError: An error occurred while trying to make a connection.

        Returns:
            dict: key is the callsign and the value is a tuple of: GridSquare, AG,\
                Last Upload
        """

        url = "https://www.eqsl.cc/DownloadedFiles/eQSLMemberList.csv"

        with requests.Session() as s:
            response = s.get(url, timeout=timeout)
            if response.status_code == requests.codes.ok:
                result_list = response.text.split("\r\n")[1:-1]
                dict_calls = {}
                for row in result_list:
                    data = row.split(",")
                    dict_calls[data[0]] = data[1:]
                return dict_calls
            raise response.raise_for_status()

    @staticmethod
    def get_users_data(callsign: str):
        """Get a specific user's data from the full member list.

        Note:
            This is incredibly slow. A better method probably involves doing some\
                vectorization, but that would require adding a dependency.

        Args:
            callsign (str): callsign to get data about

        Returns:
            tuple: contains: GridSquare, AG, Last Upload
        """
        dict_users: dict = eQSLClient.get_full_member_list()
        return dict_users.get(callsign)

    # endregion


# endregion
