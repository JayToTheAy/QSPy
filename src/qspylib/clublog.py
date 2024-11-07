# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import requests
from qspylib.logbook import Logbook

class ClubLogWrapper:
    """
    API wrapper for ClubLog. At present, only handles fetching QSOs.
    Fetching returns a Logbook object that must be assigned to something.
    """

    def __init__(self, email: str, callsign: str, password: str):
        self.email = email
        self.callsign = callsign
        self.password = password
        self.base_url = "https://clublog.org/getadif.php"
    
    def fetch_logbook(self):
        data = {
            'email': self.email,
            'password': self.password,
            'call': self.callsign
        }
        # filter down to only used params
        data = {k: v for k, v in data.items() if v is not None}

        response = requests.post(self.base_url, data=data)
        if response.status_code == 200:
            return Logbook(self.callsign, response.text)
        else:
            response.raise_for_status()