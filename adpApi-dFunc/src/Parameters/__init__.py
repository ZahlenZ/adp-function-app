import traceback

from datetime import datetime

from SharedCode.Config import kv_names
from SharedCode.Decorate import log_execution
from SharedCode.KVAid import KVHelper
from SharedCode.LogIt import logger
from SharedCode.Patch import teams_notification


@log_execution(func_name="Parameters")
def main(Parameters: None) -> dict:
    """Sets the credentials/parameter values from the KeyVault for all subsequent calls in the application
    Returns:
        {
            adp_credentials:
                certificate,
                private_key,
                client_id,
                client_secret,
                user,
                password
            edw_credentials:
                user,
                password,
                port,
                host,
                db_name,
                driver
            query:
                skip,
                top
        }
    """
    try:
        kv_help = KVHelper(*kv_names)
        datv_credentials = kv_help.get_datv_credentials()
        adp_credentials = {
            "certificate": kv_help.get_certficate(),
            "private_key": kv_help.get_private_key(),
            "client_id": kv_help.get_client_id(),
            "client_secret": kv_help.get_client_secret(),
        }
        edw_credentials = {
            "user": kv_help.get_srvc_user(),
            "password": kv_help.get_srvc_pass(),
            "port": datv_credentials["db_port"],
            "host": datv_credentials["db_host"],
            "db_name": datv_credentials["db_name"],
            "driver": "ODBC Driver 17 for SQL Server",
        }
        query = {
            "skip": 0,
            "top": 200,
        }
        return {
            "adp_credentials": adp_credentials,
            "edw_credentials": edw_credentials,
            "query": query,
            "token_time": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logger.exception(
            f"Unknown error retrieving keyvault items. \n\n\
            ERROR: {str(er)}. \n\n\
            TRACEBACK: {traceback.format_exc()}",
            extra=properties
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params={"edw_credentials": {"host": None}})
        raise er
