# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the ClubLog API.
"""
import requests
from .logbook import Logbook


class ClubLogError(Exception):
    """An error raised when an issue occurs with the ClubLog API."""

    def __init__(
        self, message="An error occurred while interfacing with the ClubLog API"
    ):
        super().__init__(message)


class ClubLogClient:
    """This is a wrapper for the ClubLog API, holding a user's authentication\
        to perform actions on their behalf.
    """

    def __init__(self, email: str, callsign: str, password: str, timeout: int = 15):
        """Initializes a ClubLogClient object.

        Args:
           email (str): Email address for the ClubLog account
           callsign (str): Callsign for the ClubLog account
           password (str): Password for the ClubLog account
           timeout (int, optional): Timeout for requests. Defaults to 15.
        """
        self.email = email
        self.callsign = callsign
        self.password = password
        self.timeout = timeout
        self.base_url = "https://clublog.org/getadif.php"

    def fetch_logbook(self) -> Logbook:
        """Fetch the user's ClubLog logbook.
        Raises:
            HTTPError: An error occurred while trying to make a connection.
        Returns:
            qspylib.logbook.Logbook: A logbook containing the user's QSOs.
        """
        data = {"email": self.email, "password": self.password, "call": self.callsign}
        # filter down to only used params
        data = {k: v for k, v in data.items() if v is not None}

        response = requests.post(self.base_url, data=data, timeout=self.timeout)
        if response.status_code == requests.codes.ok:
            return Logbook(self.callsign, response.text)
        raise response.raise_for_status()
