# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the QRZ APIs.
"""
# region Imports
import html
from collections import OrderedDict
from typing import Any
from urllib.parse import urlparse, parse_qs
from re import findall
import requests
import xmltodict
import adif_io
from .logbook import Logbook
from ._version import __version__


# constants
MAX_NUM_RETRIES = 1
# endregion


# region Exceptions
class QRZInvalidSessionError(Exception):
    """Error for when session is invalid."""

    def __init__(
        self,
        message="Got no session key back. This session is\
                invalid.",
    ):
        self.message = message
        super().__init__(self, message)


class QRZLogbookError(Exception):
    """Error for when a logbook error occurs."""

    def __init__(
        self,
        message="An error occurred interacting with the Logbook.",
    ):
        self.message = message
        super().__init__(self, message)


# endregion


# region Logbook Client
class QRZLogbookClient:
    """API wrapper for accessing QRZ Logbook data."""

    def __init__(self, key: str, timeout: int = 15):
        """Initializes a QRZLogbookClient object.

        Args:
            key (str): API key for a QRZ logbook.
            timeout (int, optional): Time in seconds to wait for a response.\
                Defaults to 15.
        """
        self.key = key
        self.base_url = "https://logbook.qrz.com/api"
        self.timeout = timeout
        self.headers = {
            "User-Agent": "pyQSP/" + __version__,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

    def fetch_logbook(self, option: str = None) -> Logbook:
        """Fetches the logbook corresponding to the Client's API Key.

        Note:
            If too many records are fetched at once, parsing will fail to\
            complete and not all response keys will be returned. To prevent\
            this, you should fetch the logbook in chunks, using the highest\
            logid to start fetching the next chunk. See fetch_logbook_paged,\
            unless that hasn't been implemented yet; then use this, and suffer.

        Args:
            option (str, optional): Optional parameters as specified by QRZ,\
            like "MODE:SSB,CALL:W1AW". This should be a comma separated string.\
            Defaults to None.

        Raises:
            HTTPError: An error occurred trying to make a connection.
            QRZLogbookError: An error occurred trying to interact with the logbook.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        data = {"KEY": self.key, "ACTION": "FETCH", "OPTION": option}
        # filter down to only used params
        data = {k: v for k, v in data.items() if v is not None}

        response = requests.post(
            self.base_url, data=data, headers=self.headers, timeout=self.timeout
        )
        if response.status_code != requests.codes.ok:
            raise response.raise_for_status()

        response_dict = parse_qs(
            urlparse("ws://a.a/?" + html.unescape(response.text))[4],
            strict_parsing=True,
        )
        if response_dict.get("RESULT")[0] == "OK":
            return QRZLogbookClient.__stringify(self, response_dict["ADIF"][0])
        else:
            raise QRZLogbookError(response_dict.get("REASON")[0])

    def delete_record(self, list_logids: list) -> dict[str, list[str]]:
        """Deletes log records from the logbook corresponding to the\
        Client's API Key.

        Note:
            This is permenant, and cannot be undone.

        Args:
            list_logids (list): A list of logid values to delete from the\
            logbook.

        Raises:
            HTTPError: An error occurred trying to make a connection.
            QRZLogbookError: An error occurred trying to interact with the logbook.

        Returns:
            dict[str, list[str]]: A dict containing the returned information\
            from QRZ. This should include the RESULT, COUNT of records\
            deleted, and LOGIDs not found, if any.
        """
        data = {"KEY": self.key, "ACTION": "DELETE", "LOGIDS": ",".join(list_logids)}
        response = requests.post(
            self.base_url, data=data, headers=self.headers, timeout=self.timeout
        )
        if response.status_code !=  requests.codes.ok:
            raise response.raise_for_status()

        response_dict = parse_qs(
            urlparse("ws://a.a/?" + html.unescape(response.text))[4],
            strict_parsing=True,
        )

        match_str = response_dict.get("RESULT")[0]

        if match_str == "OK":
            return {
                "RESULT": response_dict.get("RESULT")[0],
                "COUNT": response_dict.get("COUNT")[0],
            }
        elif match_str == "PARTIAL":
            return {
                "RESULT": response_dict.get("RESULT")[0],
                "COUNT": response_dict.get("COUNT")[0],
                "LOGIDS": QRZLogbookClient.convert_logids_to_list(
                    response_dict.get("LOGIDS")
                ),
            }
        elif match_str == "FAIL":
            raise QRZLogbookError(response_dict.get("REASON")[0])
        else:
            raise QRZLogbookError(
                "An invalid state was reached with no known error."
            )

    def insert_record(self, adif: adif_io.QSO, option: str = None) -> list:
        """Insert records into the logbook corresponding to the Client's API Key.

        Args:
            adif (adif_io.QSO): adif_io.QSO object to insert into the logbook.
            option (str, optional): REPLACE To automatically overwrite any existing\
                QSOs. Defaults to None.

        Raises:
            QRZLogbookError: The logbook API returned an error, and the reason is included.
            QRZLogbookError: An unknown condition was reached with the logbook API.
            HTTPError: An error occurred trying to make a connection.

        Returns:
            list: list of logids for records that were inserted or replaced.
        """
        data = {
            "KEY": self.key,
            "ACTION": "INSERT",
            "ADIF": str(adif),
            "OPTION": option,
        }
        response = requests.post(
            self.base_url, data=data, headers=self.headers, timeout=self.timeout
        )
        if response.status_code != requests.codes.ok:
            raise response.raise_for_status()

        response_dict = parse_qs(
            urlparse("ws://a.a/?" + html.unescape(response.text))[4],
            strict_parsing=True,
        )
        match_str = response_dict.get("RESULT")[0]

        if match_str == "OK":
            return QRZLogbookClient.convert_logids_to_list(
                response_dict["LOGID"][0]
            )
        elif match_str == "REPLACE":
            return QRZLogbookClient.convert_logids_to_list(
                response_dict["LOGID"][0]
            )
        elif match_str == "FAIL":
            raise QRZLogbookError(str(response_dict.get("REASON")[0]))
        else:
            raise QRZLogbookError("Unknown error occurred.")

    def check_status(self, list_logids: list = None) -> dict[str, list[str]]:
        """Gets the status of a logbook based on the API Key supplied\
        to the Client. This status can include information about the logbook\
        like the owner, logbook name, DXCC count, confirmed QSOs, start and\
        end date, etc.

        Args:
            list_logids (list, optional): A list of LOGIDs. Defaults to None.

        Raises:
            HTTPError: An error occurred trying to make a connection.
            QRZLogbookError: An error occurred trying to interact with the logbook.

        Returns:
            dict[str, list[str]]: A dict containing the returned status\
            information from QRZ. Keys correspond to the name given to the\
            field by QRZ's API, e.g. DXCC count is 'DXCC_COUNT', confirmed\
            is 'CONFIRMED', etc.
        """
        if list_logids is None:
            data = {"KEY": self.key, "ACTION": "STATUS"}
        else:
            data = {
                "KEY": self.key,
                "ACTION": "STATUS",
                "LOGIDS": ",".join(
                    QRZLogbookClient.convert_logids_to_list(list_logids)
                ),
            }

        response = requests.post(
            self.base_url, data=data, headers=self.headers, timeout=self.timeout
        )
        if response.status_code != requests.codes.ok:
            raise response.raise_for_status()

        response_dict = parse_qs(
            urlparse("ws://a.a/?" + html.unescape(response.text))[4],
            strict_parsing=True,
        )
        if response_dict.get("RESULT")[0] == "OK":
            result = {}
            for kvp in response_dict.items():
                result[kvp[0]] = kvp[1][0]
            return result
        else:
            raise QRZLogbookError(response_dict.get("REASON")[0])

    ### Helpers
    def __stringify(self, adi_log) -> Logbook:
        log_adi = (
            "<EOH>" + adi_log
        )  # adif_io expects a header, so we're giving it an end of header
        return Logbook(self.key, log_adi)

    @staticmethod
    def convert_logids_to_list(logids: str) -> list:
        """When QRZ returns a list of logids, they are returned as a weird, gross\
        string. This parses that and returns an actual list of the integers.

        Args:
            logids (str): list of logids as generated by QRZ's API

        Returns:
            list: actual list of integer logids
        """
        regex = r"\d+"
        return findall(regex, logids)


# endregion


# region XML Client
class QRZXMLClient:
    """A wrapper for the QRZ XML interface.
    This functionality requires being logged in and maintaining a session.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        agent: str = None,
        timeout: int = 15,
    ):
        """Creates a QRZXMLClient object.

        Todo: Change this to use a session key instead of username/password.

        Args:
            username (str, optional): username for QRZ user account.\
                Defaults to None.
            password (str, optional): password for QRZ user account.\
                Defaults to None.
            agent (str, optional): User agent string to use for requests.\
                This should identify the program responsible for this request,\
                so QRZ can hunt you down if your program breaks and spams\
                them. Defaults to None.
            timeout (int, optional): Time in seconds to wait for a response.\
                Defaults to 15.

        Raises:
            QRZInvalidSessionError: An error occurred trying to instantiate a session.
        """
        self.username = username
        self.password = password
        self.agent = agent if agent is not None else "pyQSP/" + __version__
        self.session_key = None
        self.timeout = timeout
        self.base_url = "https://xmldata.qrz.com/xml/1.34/"
        self.headers = {
            "User-Agent": self.agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive",
        }

        self._initiate_session()

    def _initiate_session(self):
        """Helper -- Grab us a session key so we're not throwing around\
            passwords"""
        params = {
            "username": self.username,
            "password": self.password,
            "agent": self.agent,
        }

        response = requests.get(
            self.base_url, params=params, headers=self.headers, timeout=self.timeout
        )
        xml_dict = xmltodict.parse(response.text)
        key = xml_dict["QRZDatabase"]["Session"].get("Key")
        if not key:
            raise QRZInvalidSessionError()

        self.session_key = key

    def _verify_session(self):
        """Helper -- Verify our session key is still valid."""
        params = {"agent": self.agent, "s": self.session_key}

        response = requests.get(
            self.base_url, params=params, headers=self.headers, timeout=self.timeout
        )
        if not xmltodict.parse(response.text)["QRZDatabase"]["Session"].get("Key"):
            raise QRZInvalidSessionError()

    def lookup_callsign(self, callsign: str) -> OrderedDict[str, Any]:
        """Looks up a callsign in the QRZ database.

        Args:
            callsign (str): Callsign to lookup.

        Raises:
            HTTPError: An error occurred trying to make a connection.
            QRZInvalidSessionError: An error occurred trying to instantiate a session.

        Returns:
            OrderedDict[str, Any]: Data on the callsign looked up, organized as
                a dict with each returned field as a key.
        """
        params = {"agent": self.agent, "s": self.session_key, "callsign": callsign}
        num_retries = 0
        while num_retries < MAX_NUM_RETRIES:
            response = requests.get(
                self.base_url, params=params, headers=self.headers, timeout=self.timeout
            )
            if response.status_code != requests.codes.ok:
                raise response.raise_for_status()

            parsed_response = xmltodict.parse(response.text)
            if not parsed_response["QRZDatabase"]["Session"].get("Key"):
                self._initiate_session()
                num_retries += 1
            else:
                return parsed_response

        # if we didn't manage to return from a logged in session, raise an error
        raise QRZInvalidSessionError(
            **{"message": parsed_response["ERROR"]}
            if parsed_response.get("ERROR")
            else {}
        )

    def lookup_dxcc(self, dxcc: str) -> OrderedDict[str, Any]:
        """Looks up a DXCC by prefix or DXCC number.

        Args:
            dxcc (str): DXCC or prefix to lookup. Note that callsigns must be\
                uppercase, or QRZ won't recognize it.

        Raises:
            HTTPError: An error occurred trying to make a connection.
            QRZInvalidSessionError: An error occurred trying to instantiate a session.

        Returns:
            OrderedDict[str, Any]: Data on the callsign looked up, organized as\
                a dict with each returned field as a key. This data includes\
                DXCC, CC, name, continent, ituzone, cqzone, timezone, lat,\
                lon, & notes
        """
        # return self.__lookup_dxcc(dxcc, 0)
        params = {"agent": self.agent, "s": self.session_key, "dxcc": dxcc}
        num_retries = 0
        while num_retries < MAX_NUM_RETRIES:
            response = requests.get(
                self.base_url, params=params, headers=self.headers, timeout=self.timeout
            )
            if response.status_code != requests.codes.ok:
                raise response.raise_for_status()

            parsed_response = xmltodict.parse(response.text)
            if not parsed_response["QRZDatabase"]["Session"].get("Key"):
                self._initiate_session()
                num_retries += 1
            else:
                return parsed_response

        # if we didn't manage to return from a logged in session, raise an error
        raise QRZInvalidSessionError(
            **{"message": parsed_response["ERROR"]}
            if parsed_response.get("ERROR")
            else {}
        )


# endregion
