import json
import logging
import traceback

from SharedCode.Config import endpoints
from SharedCode.Decorate import log_execution
from SharedCode.KVAid import make_certificate, make_key
from SharedCode.LogIt import logger
from SharedCode.Patch import post_request, teams_notification


@log_execution(func_name="ADPOpenConnection")
def main(ADPOpenConnection: dict) -> dict:
    """Open the connection to ADP Server and retrieve an Auth Token

    Args:
        ADPOpenConnection (dict): {
        adp_credentials -> from parameters
        edw_credentials -> from paramters
        query -> from parameters}

    Returns:
        token: auth token
    """
    adp_credentials = ADPOpenConnection["adp_credentials"]

    cert = make_certificate(adp_credentials["certificate"])
    key = make_key(adp_credentials["private_key"])

    form_data = {
        "grant_type": "client_credentials",
        "client_id": adp_credentials["client_id"],
        "client_secret": adp_credentials["client_secret"],
    }
    headers = {"user-agent": "cd-adpApi-func-python/1.0.0"}

    try:
        r = post_request(
            url=endpoints.auth_url,
            headers=headers,
            cert=(cert, key),
            data=form_data,
            module_name=__name__,
        )
        return {
            "bearer_token": json.loads(r.content)["access_token"],
            "status": r.status_code,
        }
    except Exception as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logger.exception(
            f"Unknown error: Unable to authentiate to ADP. \n\n\
            ERROR: {str(er)}.\n\n\
            TRACEBACK: {traceback.format_exc()}",
            extra=properties
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params=ADPOpenConnection)
        raise er
