import requests
from SharedCode.Patch import _is_key_file_encrypted, patch_requests
from unittest.mock import MagicMock, patch
from OpenSSL.crypto import PKey
from OpenSSL.crypto import TYPE_RSA
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def test_patch_requests_with_adapter():
    ssl_module_mock = MagicMock()
    ssl_module_mock._is_key_file_encrypted = MagicMock()
    ssl_module_mock.PyOpenSSLContext = MagicMock()
    http_adapter_mock = MagicMock()

    with patch("requests.packages.urllib3.util.ssl_", ssl_module_mock):
        with patch("requests.sessions.HTTPAdapter", http_adapter_mock):
            patch_requests(adapter=True)

    r = requests.get("https://httpbin.org/get")
    assert r.status_code == 200
