import json
import logging
import requests
import traceback

from OpenSSL.crypto import PKCS12, X509, PKey
from urllib3.contrib import pyopenssl

from SharedCode.Config import adaptive_card, adaptive_card_url
from SharedCode.Decorate import retry
from SharedCode.LogIt import logger


def _is_key_file_encrypted(keyfile):
    """
    In memory key is not encrypted
    """
    if isinstance(keyfile, PKey):
        return False
    return _is_key_file_encrypted.original(keyfile)


class PyOpenSSLContext(pyopenssl.PyOpenSSLContext):
    """
    Support loading certs from memory
    """

    def load_cert_chain(self, certfile, keyfile=None, password=None):
        if isinstance(certfile, X509) and isinstance(keyfile, PKey):
            self._ctx.use_certificate(certfile)
            self._ctx.use_privatekey(keyfile)
        else:
            super().load_cert_chain(certfile, keyfile=keyfile, password=password)


class HTTPAdapter(requests.adapters.HTTPAdapter):
    """
    Handle a variety of cert types
    """

    def cert_verify(self, conn, url, verify, cert):
        if cert:
            # PKCS12
            if isinstance(cert, PKCS12):
                conn.cert_file = cert.get_certificate()
                conn.key_file = cert.get_privatekey()
                cert = None
            elif isinstance(cert, tuple) and len(cert) == 2:
                # X509 and PKey
                if isinstance(cert[0], X509) and hasattr(cert[1], PKey):
                    conn.cert_file = cert[0]
                    conn.key_file = cert[1]
                    cert = None
                # cryptography objects
                elif hasattr(cert[0], "public_bytes") and hasattr(
                    cert[1], "private_bytes"
                ):
                    conn.cert_file = X509.from_cryptography(cert[0])
                    conn.key_file = PKey.from_cryptography_key(cert[1])
                    cert = None
        super().cert_verify(conn, url, verify, cert)


def patch_requests(adapter=True):
    """
    You can perform a full patch and use requests as usual:
    patch_requests()
    requests.get('https://httpbin.org/get')

    or use the adapter explicitly:
    patch_requests(adapter=False)
    session = requests.Session()
    session.mount('https', HTTPAdapter())
    session.get('https://httpbin.org/get')
    """
    if hasattr(requests.packages.urllib3.util.ssl_, "_is_key_file_encrypted"):
        _is_key_file_encrypted.original = (
            requests.packages.urllib3.util.ssl_._is_key_file_encrypted
        )
        requests.packages.urllib3.util.ssl_._is_key_file_encrypted = (
            _is_key_file_encrypted
        )
    requests.packages.urllib3.util.ssl_.SSLContext = PyOpenSSLContext
    if adapter:
        requests.sessions.HTTPAdapter = HTTPAdapter


# Build in retries for all post requests
@retry()
def post_request(url, headers, cert=None, auth=None, data=None, module_name=None):
    """post request with built in Retries and Error Propagation from retry decorator

    Args:
        module_name (__name__): utilize __name__ to inject the name of the module making the call

    Returns:
        _type_: response
    """
    patch_requests()
    return requests.post(url=url, headers=headers, cert=cert, auth=auth, data=data)


# Build in retries for all get requests
@retry(max_tries=12, delay_seconds=3)
def get_request(
    url, headers, params=None, cert=None, auth=None, data=None, module_name=None
):
    """get request with built in Retries and Error Propagation from retry decorator

    Args:
        module_name (__name__): utilize __name__ to inject the name of the module making the call

    Returns:
        _type_: response
    """
    patch_requests()
    return requests.get(
        url=url, headers=headers, params=params, auth=auth, cert=cert, data=data
    )


# Class to handle not getting a 201 response from authentication call to Anaplan
class Non201ResponseError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code

    def __str__(self):
        return f"Unexpected response status code: {self.status_code}. Expected status code: 201."


def teams_notification(status, params, base_card=adaptive_card, url=adaptive_card_url):
    headers = {"Content-Type": "application/json"}

    base_card["attachments"][0]["content"]["body"][1]["text"] = base_card[
        "attachments"
    ][0]["content"]["body"][1]["text"].format(target=params["edw_credentials"]["host"])

    base_card["attachments"][0]["content"]["body"][2]["text"] = base_card[
        "attachments"
    ][0]["content"]["body"][2]["text"].format(
        status=status["status"], worker_count=status["worker_count"]
    )

    base_card["attachments"][0]["content"]["body"][3]["text"] = base_card[
        "attachments"
    ][0]["content"]["body"][3]["text"].format(message=status["message"])

    try:
        r = requests.post(url=url, data=json.dumps(base_card), headers=headers)
    except Exception as er:
        logging.debug(f"error {str(er)}")
        logger.exception(
            f"Failed to send teams notification. \n\n\
            ERROR: {str(er)}. \n\n\
            TRACEBACK: {traceback.format_exc()}"
        )
        raise er
