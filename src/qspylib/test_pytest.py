# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""A PyTest module for confirming functionality works None of these should be
called; these are automatically ran by PyTest when pushes are made to the repo,
or when the user runs `pytest` in the root directory of the project.
"""
import adif_io
import pytest
import qspylib.logbook
from qspylib import eqsl
from qspylib import lotw
# from qspylib import qrz


#################
# logbook tests #
#################
def test_equality_of_qso():
    """Tests equality of qspylib.logbook.QSOs functions as expected"""
    adif_qso = adif_io.QSO(
        {
            "CALL": "W1AW",
            "BAND": "20m",
            "MODE": "SSB",
            "QSO_DATE": "20220101",
            "TIME_ON": "0000",
            "QSL_RCVD": "N",
        }
    )
    qso1 = qspylib.logbook.QSO("W1AW", "20m", "SSB", "20220101", "0000", "N")
    qso2 = qspylib.logbook.qso_from_adi(adif_qso)
    assert qso1 == qso2


def test_inequality_of_qso():
    """Tests inequality of qspylib.logbook.QSOs functions as expected"""
    adif_qso = adif_io.QSO(
        {
            "CALL": "W1AW/4",
            "BAND": "20m",
            "MODE": "SSB",
            "QSO_DATE": "20220101",
            "TIME_ON": "0000",
            "QSL_RCVD": "N",
        }
    )
    qso1 = qspylib.logbook.QSO("W1AW", "20m", "SSB", "20220101", "0000", "N")
    qso2 = qspylib.logbook.qso_from_adi(adif_qso)
    assert qso1 != qso2


def test_generating_a_logbook():
    """Test generating a qspylib.logbook.Logbook"""
    adif_string = "a header\
<eoh>\
\
<CALL:4>CA7LLSIGN\
<BAND:3>20M\
<FREQ:8>14.20000\
<MODE:3>FT8\
<QSO_DATE:8>20240101\
<TIME_ON:6>104500\
<QSL_RCVD:1>Y\
<QSLRDATE:8>20240102\
<eor>"
    log = qspylib.logbook.Logbook("TE5T", adif_string)
    assert isinstance(log, qspylib.logbook.Logbook)


def test_logbook_attributes_match():
    """Confirm that the Logbook's stored QSO matches what we read from text"""
    adif_string = "a header\
<eoh>\
\
<CALL:4>CA7LLSIGN\
<BAND:3>20M\
<FREQ:8>14.20000\
<MODE:3>FT8\
<QSO_DATE:8>20240101\
<TIME_ON:6>104500\
<QSL_RCVD:1>Y\
<QSLRDATE:8>20240102\
<eor>"
    log = qspylib.logbook.Logbook("TE5T", adif_string)
    assert log.log[0] == qspylib.logbook.qso_from_adi(log.adi[0])


def test_adding_and_removing():
    """Test adding and removing a QSO"""
    adif_string = "a header\
<eoh>\
\
<CALL:4>CA7LLSIGN\
<BAND:3>20M\
<FREQ:8>14.20000\
<MODE:3>FT8\
<QSO_DATE:8>20240101\
<TIME_ON:6>104500\
<QSL_RCVD:1>Y\
<QSLRDATE:8>20240102\
<eor>"
    log = qspylib.logbook.Logbook("TE5T", adif_string)
    new_adif_qso = adif_io.QSO(
        {
            "CALL": "W1AW/5",
            "BAND": "20m",
            "MODE": "SSB",
            "QSO_DATE": "20220101",
            "TIME_ON": "0000",
            "QSL_RCVD": "N",
        }
    )
    log.write_qso(new_adif_qso)
    log.discard_qso(log.adi[0])
    assert (
        len(log.log) == 1
        and len(log.adi) == 1
        and log.adi[0]["CALL"] == "W1AW/5"
        and log.log[0].their_call == "W1AW/5"
    )


##############
# lotw tests #
##############


def test_pull_a_call_from_last_upload():
    """Test pulling a known call from the last upload"""
    last_uploads = lotw.LOTWClient.get_last_upload()
    assert "W1AW" in last_uploads


def test_bad_login_fetch():
    """Test fetching a logbook with a bad login"""
    with pytest.raises(lotw.RetrievalFailure):
        lotw_obj = lotw.LOTWClient("**notavalidcall**", "**notarealpassword**")
        lotw_obj.fetch_logbook()


def test_bad_login_dxcc():
    """Test fetching DXCC credits with a bad login"""
    with pytest.raises(lotw.RetrievalFailure):
        lotw_obj = lotw.LOTWClient("**notavalidcall**", "**notarealpassword**")
        lotw_obj.get_dxcc_credit()


###############
#  eqsl tests #
###############


def test_verify_a_bad_eqsl():
    """Test verifying a known bad eqsl"""
    is_qsl_real, result = eqsl.eQSLClient.verify_eqsl(
        "N5UP", "TEST", "160m", "SSB", "01/01/2000"
    )
    assert "Error - Result: QSO not on file" in result and is_qsl_real is False


def test_verify_a_good_eqsl():
    """Test verifying a known good eqsl"""
    is_qsl_real, result = eqsl.eQSLClient.verify_eqsl(
        "ai5zk", "w1tjl", "10m", "SSB", "01/20/2024"
    )
    assert "Result - QSO on file" in result and is_qsl_real is True


def test_pull_a_known_ag_call():
    """Test grabbing a call we know should be in the AG list"""
    callsigns = eqsl.eQSLClient.get_ag_list()
    assert "W1AW" in callsigns[0]


def test_pull_a_known_nonag_call():
    """Test grabbing a call we know shouldn't be in the AG list"""
    callsigns = eqsl.eQSLClient.get_ag_list()
    assert "WE3BS" not in callsigns[0]


def test_pull_a_call_from_ag_dated():
    """Test grabbing a call from the AG dated list"""
    callsigns = eqsl.eQSLClient.get_ag_list_dated()
    assert callsigns[0].get("W1AW") >= "0000-00-00"


def test_pull_a_known_call_from_total_members():
    """Test grabbing a call that should be in the list of total members"""
    all_users = eqsl.eQSLClient.get_full_member_list()
    assert all_users.get("W1AW")


def test_pull_a_missing_call_from_total_members():
    """Test grabbing a call that should be missing from the list of total members"""
    all_users = eqsl.eQSLClient.get_full_member_list()
    assert not all_users.get("WE3BS")


def test_get_user_data():
    """Test getting the data of a user, and verify it's what we expect"""
    user = eqsl.eQSLClient.get_users_data("W1AW")
    assert user[0] == "FN31pr" and user[1] == "Y" and not user[2]


#############
# qrz tests #
#############

# def test_qrz_xml_with_invalid_key():
#    log_obj = qrz.QRZLogbookAPI('aaaaaaaaaaaaa')
#    log = log_obj.fetch_logbook()
