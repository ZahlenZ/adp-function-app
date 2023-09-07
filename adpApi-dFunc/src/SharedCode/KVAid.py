import json
import logging
import traceback

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from azure.keyvault.certificates import CertificateClient, KeyVaultCertificate
from azure.keyvault.certificates._models import KeyVaultCertificate
from azure.keyvault.keys import KeyClient
from azure.keyvault.secrets import KeyVaultSecret, SecretClient
from azure.keyvault.secrets._models import KeyVaultSecret
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from SharedCode import LogIt

logger = logging.getLogger("func")


def string_it(azure_object: KeyVaultCertificate or KeyVaultSecret) -> str:
    """Turn a KeyVaultObject into a json serializable string to be passed between activity functions

    Args:
        azure_object (KeyVaultCertificate or KeyVaultSecret)

    Returns:
        str: cert or key string
    """
    if isinstance(azure_object, KeyVaultSecret):
        return json.dumps(azure_object.value)
    elif isinstance(azure_object, KeyVaultCertificate):
        return bytes(azure_object.cer).decode("latin1")
    else:
        logging.info(f"{azure_object} not correct type")


# no test - the object this function transforms is hard to replicate.
def make_certificate(certificate_string: str) -> object:  # pragma: no cover
    """Take certificate string and return a usable certificate for TLS authentication

    Args:
        certificate_string (str): json serializaable string

    Returns:
        object: TLS Certificate
    """

    try:
        return x509.load_der_x509_certificate(
            bytes(certificate_string.encode("latin1"))
        )
    except TypeError as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logging.info(
            f"{certificate_string} not correct type.\n\n\
            ERROR: {str(er)}\n\n\
            TRACEBACK:{traceback.format_exc()}",
            extra=properties
        )


# no test - the object this function transforms is hard to replicate.
def make_key(private_key_string: str) -> object:  # pragma: no cover
    """Take a key string and return a usable key for TLS authentication

    Args:
        private_key_string (str): json serializable string

    Returns:
        object: TLS Authentication Key
    """

    try:
        key = json.loads(private_key_string)
        return serialization.load_pem_private_key(key.encode(), password=None)
    except TypeError as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logging.info(
            f"{private_key_string} not correct type.\n\n\
            ERROR: {str(er)}\n\n\
            TRACEBACK:{traceback.format_exc()}",
            extra=properties
        )


class KVHelper:
    # Set KV connection credentials
    def __init__(
        self,
        kv_name,
        kv_client_id,
        kv_client_secret,
        kv_certificate,
        db_name,
        db_user,
        db_pass,
        db_host,
        db_port,
    ):
        self.kv_name = kv_name
        self.kv_url = f"https://{self.kv_name}.vault.azure.net"
        self.az_credentials = DefaultAzureCredential(
            additionally_allowed_tenants=["*"],
            exclude_shared_token_cache_credential=True,
        )
        self.secret_client = SecretClient(
            vault_url=self.kv_url, credential=self.az_credentials
        )
        self.cert_client = CertificateClient(
            vault_url=self.kv_url, credential=self.az_credentials
        )
        # Set Names of KeyVault Objects
        self.client_id = kv_client_id
        self.client_secret = kv_client_secret
        self.certificate = kv_certificate
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_host = db_host
        self.db_port = db_port

    def get_srvc_user(self) -> str:
        """Retrieve User Name for a service account
        Raises:
            er: ClientAuthenticationError

        Returns:
            str: {user_name : {user_name}}
        """
        try:
            return self.secret_client.get_secret(self.db_user).value
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logger.critical(
                f"Couldn't authenticate to {self.kv_name} from {__class__}.\n\n\
                ERROR: {str(er)}\n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )
            raise er

    def get_srvc_pass(self) -> str:
        """Retriever password for a service account
        Raises:
            er: ClientAuthenticationError

        Returns:
            str: {pass : {password}}
        """
        try:
            return self.secret_client.get_secret(self.db_pass).value
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logger.critical(
                f"Couldn't authenticate to {self.kv_name} from {__class__}\n\n\
                ERROR: {str(er)}\n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )
            raise er

    def get_datv_credentials(self) -> dict:
        """Retrieve datv credentials from Azure Key Vault

        Raises:
            er: ClientAuthenticationError

        Returns:
            dict: {db_user, db_pass, db_port, db_host}
        """
        try:
            return {
                "db_user": self.secret_client.get_secret(self.db_user).value,
                "db_pass": self.secret_client.get_secret(self.db_pass).value,
                "db_port": self.secret_client.get_secret(self.db_port).value,
                "db_host": self.secret_client.get_secret(self.db_host).value,
                "db_name": self.db_name,
            }
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logging.critical(
                f"Couldn't authenticate to {self.kv_name} from {__class__}\n\n\
                ERROR: {str(er)}\n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )
            raise er

    def get_certficate(self) -> str:
        """Retrieve ADP TLS certificate from Azure Key Vault and turn into a JSON serializable string

        Returns:
            str: Certificate string
        """
        try:
            cert = self.cert_client.get_certificate(self.certificate)
            return string_it(cert)
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logging.critical(
                f"Couldn't authenticate to {self.kv_name}.\n\n\
                ERROR: {str(er)}\n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )

    def get_private_key(self) -> str:
        """Retrieve ADP TLS private key from Azure Key Vault and turn into a JSON serializable string

        Returns:
            str: private key string
        """
        try:
            key = self.secret_client.get_secret(self.certificate)
            return string_it(key)
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logging.exception(
                f"Couldn't authenticate to {self.kv_name}.\n\n\
                ERROR: {str(er)}. \n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )

    def get_client_id(self) -> str:
        """Retrieve client id for API calls to ADP API

        Returns:
            str: client id
        """
        try:
            return self.secret_client.get_secret(self.client_id).value
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logging.exception(
                f"Couldn't authenticate to {self.kv_name}. \n\n\
                ERROR: {str(er)}. \n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )

    def get_client_secret(self) -> str:
        """Retrieve client secret for API calls to ADP API

        Returns:
            str: client secret
        """
        try:
            return self.secret_client.get_secret(self.client_secret).value
        except ClientAuthenticationError as er:
            properties = {"custom_dimensions": {"app": "ADP"}}
            logging.exception(
                f"Couldn't authenticate to {self.kv_name}. \n\n\
                ERROR: {str(er)}. \n\n\
                TRACEBACK: {traceback.format_exc()}",
                extra=properties
            )
