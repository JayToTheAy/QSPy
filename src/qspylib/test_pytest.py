# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
import qspylib.eqsl as eqsl
import qspylib.lotw as lotw
import qspylib.qrz as qrz

##############
# lotw tests #
##############

def test_pull_a_call_from_last_upload():
    last_uploads = lotw.get_last_upload()
    assert 'W1AW' in last_uploads

def test_bad_login_fetch():
    with pytest.raises(lotw.RetrievalFailure):
        lotw_obj = lotw.LOTWSession('**notavalidcall**', '**notarealpassword**')
        lotw_obj.fetch_logbook()

def test_bad_login_dxcc():
    with pytest.raises(lotw.RetrievalFailure):
        lotw_obj = lotw.LOTWSession('**notavalidcall**', '**notarealpassword**')
        lotw_obj.get_dxcc_credit()

###############
#  eqsl tests #
###############

def test_verify_a_bad_eqsl():
    is_qsl_real, result = eqsl.verify_eqsl('N5UP', 'TEST', '160m', 'SSB', '01/01/2000')
    assert 'Error - Result: QSO not on file' in result and is_qsl_real is False

def test_verify_a_good_eqsl():
    is_qsl_real, result = eqsl.verify_eqsl('ai5zk', 'w1tjl', '10m', 'SSB', '01/20/2024')
    assert 'Result - QSO on file' in result and is_qsl_real is True

def test_pull_a_known_ag_call():
    callsigns, date = eqsl.get_ag_list()
    assert 'W1AW' in callsigns

def test_pull_a_known_nonag_call():
    callsigns, date = eqsl.get_ag_list()
    assert 'WE3BS' not in callsigns

def test_pull_a_call_from_ag_dated():
    callsigns, date = eqsl.get_ag_list_dated()
    assert callsigns.get('W1AW')  >= '0000-00-00'

def test_pull_a_known_call_from_total_members():
    all_users = eqsl.get_full_member_list()
    assert all_users.get('W1AW')

def test_pull_a_missing_call_from_total_members():
    all_users = eqsl.get_full_member_list()
    assert not all_users.get('WE3BS')

def test_get_user_data():
    user = eqsl.get_users_data('W1AW')
    assert user[0] == 'FN31pr' and user[1] == 'Y' and not user[2]

#############
# qrz tests #
#############

#def test_qrz_xml_with_invalid_key():
#    log_obj = qrz.QRZLogbookAPI('aaaaaaaaaaaaa')
#    log = log_obj.fetch_logbook()

