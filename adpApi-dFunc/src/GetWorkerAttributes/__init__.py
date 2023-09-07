import json
import traceback

import requests
from requests.exceptions import SSLError
from urllib3.util.retry import Retry

from SharedCode.Config import endpoints, queries
from SharedCode.KVAid import make_certificate, make_key
from SharedCode.LogIt import logger
from SharedCode.Patch import get_request, teams_notification


def main(GetWorkerAttributes: list) -> dict:
    """Get all non-custom attributes for chunks of 200 workers at a time. Status 204 returned when no more workers are available.

    Args:
        GetWorkerAttributes (list): (parameters, token)

    Returns:
        dict: {status: , workers: }
    """
    adp_credentials = GetWorkerAttributes[0]["adp_credentials"]
    query = GetWorkerAttributes[0]["query"]
    token = GetWorkerAttributes[1]
    cert = make_certificate(adp_credentials["certificate"])
    key = make_key(adp_credentials["private_key"])
    url = endpoints.select_url

    params = {
        "$select": queries.base_select,
        "$skip": query["skip"],
        "$top": query["top"],
    }
    headers = {
        "user-agent": "cd-adpApi-func-python/1.0.0",
        "Authorization": f"Bearer {token['bearer_token']}",
        "accept": "application/json;masked=false",
    }
    form_data = {
        "grant_type": "client_credentials",
        "client_id": adp_credentials["client_id"],
        "client_secret": adp_credentials["client_secret"],
    }

    try:
        r = get_request(
            url=url,
            headers=headers,
            params=params,
            cert=(cert, key),
            data=form_data,
            module_name=__name__,
        )

        try:
            workers = json.loads(r.content).get("workers")
            status_code = r.status_code
        except ValueError as er:
            workers = []
            status_code = r.status_code

    except SSLError as er:
        properties = {'custom_dimensions': {'app': 'ADP'}}
        logger.exception(
            f"SSL Error occured in {__name__} during http request. \n\n\
            ERROR: {str(er)} \n\n\
            TRACEBACK: {traceback.format_exc()}",
            extra=properties
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params=GetWorkerAttributes[0])
        raise er

    return {"workers": workers, "status": status_code}
