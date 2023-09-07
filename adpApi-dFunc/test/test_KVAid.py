import json
import pytest
from unittest.mock import Mock, patch

from azure.core.exceptions import ClientAuthenticationError
from azure.keyvault.certificates import KeyVaultCertificate
from azure.keyvault.secrets import KeyVaultSecret

from src.SharedCode.KVAid import string_it, KVHelper
from src.SharedCode.Config import kv_names


def test_string_it():
    cert = Mock(spec=KeyVaultCertificate)
    cert.cer = b"mock_certificate"

    result = string_it(cert)
    assert result == "mock_certificate"

    secret = Mock(spec=KeyVaultSecret)
    secret.value = {"username": "mock_username", "password": "mock_password"}

    result = string_it(secret)
    assert result == json.dumps(secret.value)

    result = string_it("wrong type")
    assert result is None


def test_get_srvc_user():
    kv_helper = KVHelper(*kv_names)
    result = kv_helper.get_srvc_user()
    assert isinstance(result, str)


def test_get_srvc_pass():
    kv_helper = KVHelper(*kv_names)
    result = kv_helper.get_srvc_pass()
    assert isinstance(result, str)


def test_get_datv_credentials():
    kv_helper = KVHelper(*kv_names)
    result = kv_helper.get_datv_credentials()

    assert isinstance(result["db_user"], str)
    assert isinstance(result["db_pass"], str)
    assert isinstance(result["db_port"], str)
    assert isinstance(result["db_host"], str)
    assert isinstance(result["db_name"], str)


@patch("azure.keyvault.secrets.SecretClient.get_secret")
def test_get_srvc_user_exception(mock_get):
    mock_get.side_effect = ClientAuthenticationError
    with pytest.raises(ClientAuthenticationError):
        kv_helper = KVHelper(*kv_names)
        kv_helper.get_srvc_user()


@patch("azure.keyvault.secrets.SecretClient.get_secret")
def test_get_srvc_pass_exception(mock_get):
    mock_get.side_effect = ClientAuthenticationError
    with pytest.raises(ClientAuthenticationError):
        kv_helper = KVHelper(*kv_names)
        kv_helper.get_srvc_pass()


@patch("azure.keyvault.secrets.SecretClient.get_secret")
def test_get_datv_credentials_exception(mock_get):
    mock_get.side_effect = ClientAuthenticationError
    with pytest.raises(ClientAuthenticationError):
        kv_helper = KVHelper(*kv_names)
        kv_helper.get_datv_credentials()
