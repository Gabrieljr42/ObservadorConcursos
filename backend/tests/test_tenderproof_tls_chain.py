import hashlib
import ssl
from pathlib import Path
import certifi
from app.tenderproof.tls_chain import source_tls_verification


def test_fumarc_only_adds_verified_intermediate_and_requires_root_and_hostname():
    normal = ssl.create_default_context(cafile=certifi.where())
    supplemented = source_tls_verification('fumarc_open')
    assert supplemented.verify_mode == ssl.CERT_REQUIRED
    assert supplemented.check_hostname
    assert not supplemented.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN
    before = {hashlib.sha256(c).hexdigest() for c in normal.get_ca_certs(binary_form=True)}
    after = {hashlib.sha256(c).hexdigest() for c in supplemented.get_ca_certs(binary_form=True)}
    assert before.issubset(after)
    assert after - before == {'b676ffa3179e8812093a1b5eafee876ae7a6aaf231078dad1bfb21cd2893764a'}


def test_other_sources_keep_standard_verification():
    assert source_tls_verification('jcm_open') is True
    assert source_tls_verification('unregistered') is True
