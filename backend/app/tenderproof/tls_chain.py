"""Supplement missing intermediate certificates without adding trust roots."""
from pathlib import Path
import ssl
import certifi


def source_tls_verification(source):
    if source != 'fumarc_open':
        return True
    # Public GlobalSign intermediate from a Windows-validated chain, 2026-09-08.
    # Its R3 root is already in certifi. Neither leaf certificates nor new roots
    # are trusted here, and partial-chain trust is explicitly disabled.
    context = ssl.create_default_context(cafile=certifi.where())
    context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_verify_locations(cafile=str(Path(__file__).parent / 'certificates' /
                                            'globalsign-rsa-ov-ssl-ca-2018.pem'))
    return context
