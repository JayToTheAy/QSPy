# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Functions and classes related to querying the QRZ APIs.
"""
import requests
import html
import xmltodict
import adif_io
from urllib.parse import urlparse, parse_qs
from .logbook import Logbook
from ._version import __version__

class QRZInvalidSession(Exception):
    """Error for when session is invalid.
    """
    def __init__(self, message="Got no session key back. This session is invalid."):
        self.message=message
        super().__init__(self, message)



class QRZLogbookClient:
    """API wrapper for a QRZ Logbook. At present, only handles fetching QSOs.
    """

    def __init__(self, key: str):
        """Initializes a QRZLogbookClient object.

        Args:
            key (str): API key for a QRZ logbook.
        """
        self.key = key
        self.base_url = "https://logbook.qrz.com/api"
        self.headers = {
            'User-Agent': 'pyQSP/' + __version__,
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }

    def fetch_logbook(self, option:str=None):
        """_summary_

        Note:
            If too many records are fetched at once, parsing will fail to complete and not all response keys will be returned.
            To prevent this, you should fetch the logbook in chunks, using the highest logid to start fetching the next chunk.
            See fetch_logbook_paged, unless that hasn't been implemented yet -- then use this, and suffer.\
            
        Args:
            option (str, optional): Optional parameters as specified by QRZ, like "MODE:SSB,CALL:W1AW". This should be a comma separated string. Defaults to None.

        Returns:
            qspylib.logbook.Logbook: A logbook containing the user’s QSOs.
        """
        data = {
            'KEY': self.key,
            'ACTION': 'FETCH',
            'OPTION': option
        }
        # filter down to only used params
        data = {k: v for k, v in data.items() if v is not None}
        
        response = requests.post(self.base_url, data=data, headers=self.headers)
        if response.status_code == requests.codes.ok:
            response_dict = parse_qs(urlparse("ws://a.a/?" + html.unescape(response.text))[4], strict_parsing=True)
            # at this point, we should have a dict of the response keys per the spec.
            return QRZLogbookClient.__stringify(self, response_dict["ADIF"])
        else:
            response.raise_for_status()

    #def fetch_logbook_paged(self, per_page:int=50, option:str=None):
    #
    #    data = {
    #        'KEY': self.key,
    #        'ACTION': 'FETCH',
    #        'OPTION': 'MAX:' + str(per_page) + "," + option
    #    }
    #    # filter down to only used params
    #    response = requests.post(self.base_url, data=data, headers=self.headers)
    #    
    #    raise NotImplementedError

    def insert_record(self, QSO:adif_io.QSO, option:str=None):
        """Inserts a single QSO into the logbook corresponding to the Client's API Key.

        Args:
            QSO (adif_io.QSO): _description_
            option (str, optional): _description_. Defaults to None.

        Raises:
            NotImplementedError: _description_
        """
        data = {
            'KEY': self.key,
            'ACTION': 'INSERT',
            'OPTION': option
        }
        raise NotImplementedError
    
    def delete_record(self, list_logids:list):
        """Deletes log records from the logbook corresponding to the Client's API Key.

        Note:
            This is permenant, and cannot be undone.

        Args:
            list_logids (list): A list of logid values to delete from the logbook.

        Returns:
            dict: A dict containing the returned information from QRZ. This should include the RESULT, COUNT of records deleted, and LOGIDs not found, if any.
        """
        data = {
            'KEY': self.key,
            'ACTION': 'DELETE',
            'LOGIDS': ','.join(list_logids)
        }
        response = requests.post(self.base_url, data=data, headers=self.headers)
        if response.status_code == requests.codes.ok:
            response_dict = parse_qs(urlparse("ws://a.a/?" + html.unescape(response.text))[4], strict_parsing=True)
            return response_dict
        else:
            response.raise_for_status()
    
    def check_status(self, list_logids:list=None):
        """Gets the status of a logbook based on the API Key supplied to the Client. This status can include information about the logbook like the owner, logbook name, DXCC count, confirmed QSOs, start and end date, etc.

        Args:
            list_logids (list, optional): A list of LOGIDs. Defaults to None.

        Returns:        
            dict: A dict containing the returned status information from QRZ. Keys correspond to the name given to the field by QRZ's API, e.g. DXCC count is 'DXCC_COUNT', confirmed is 'CONFIRMED', etc.
        """
        data = {
            'KEY': self.key,
            'ACTION': 'STATUS',
            'LOGIDS': ','.join(list_logids)
        }
        
        response = requests.post(self.base_url, data=data, headers=self.headers)
        if response.status_code == requests.codes.ok:
            response_dict = parse_qs(urlparse("ws://a.a/?" + html.unescape(response.text))[4], strict_parsing=True)
            return response_dict
        else:
            response.raise_for_status()
    

    
    ### Helpers

    def __stringify(self, adi_log):
        #qrz_output = html.unescape(adi_log)
        #start_of_log, end_of_log = qrz_output.index('ADIF=') + 5, qrz_output.rindex('<eor>\n\n') + 4
        log_adi = "<EOH>" + adi_log #adif_io expects a header, so we're giving it an end of header
        return Logbook(self.key, log_adi)
    
class QRZXMLClient:
    """A wrapper for the QRZ XML interface.
    This functionality requires being logged in and maintaining a session.
    """

    def __init__(self, username:str=None, password:str=None):
        """Creates a QRZXMLClient object.

        Todo: Change this to use a session key instead of username/password.

        Args:
            username (str, optional): username for QRZ user account. Defaults to None.
            password (str, optional): password for QRZ user account. Defaults to None.
        """
        self.username = username,
        self.password = password,
        self.agent = 'pyQSP/' + __version__
        self.session_key = None
        self.base_url = "https://xmldata.qrz.com/xml/1.34/"
        self.headers = {
            'User-Agent': self.agent,
            'Accept-Encoding': 'gzip, deflate',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }

        self.__initiate_session()
    
    def get_from_api(*args, **kwargs):
        return
        

    def __initiate_session(self):
        """Helper -- Grab us a session key so we're not throwing around passwords"""
        params = {'username': self.username,
                  'password': self.password,
                  'agent': self.agent}

        response = requests.get(self.base_url, params=params, headers=self.headers)
        xml_dict = xmltodict.parse(response.text)
        key = xml_dict["QRZDatabase"]["Session"].get("Key")
        if not key:
            raise QRZInvalidSession()
        else:
            self.session_key = key

    def __verify_session(self):
        """ Helper -- Verify our session key is still valid."""
        params = {'agent': self.agent,
                  's': self.session_key}

        response = requests.get(self.base_url, params=params, headers=self.headers)
        if not xmltodict.parse(response.text)["QRZDatabase"]["Session"].get("Key"):
            raise QRZInvalidSession()


