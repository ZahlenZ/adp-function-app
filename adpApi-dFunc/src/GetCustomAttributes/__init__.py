import json
import requests
import traceback

from requests.adapters import Retry
from requests.exceptions import SSLError

from SharedCode.Config import endpoints, queries
from SharedCode.KVAid import make_certificate, make_key
from SharedCode.LogIt import logger
from SharedCode.Patch import (
    get_request,
    teams_notification,
    HTTPAdapter,
    patch_requests,
)


def main(GetCustomAttributes: list) -> list:  # sourcery skip: extract-method
    """Gathers the custom attributes from the ADP API for a single worker

    Args:
        GetCustomAttributes (list): parameters, token, single aoid

    Returns:
        list: aoid and custom attributes
    """
    parameters = GetCustomAttributes[0]
    token = GetCustomAttributes[1]
    aoid = GetCustomAttributes[2]
    cert = make_certificate(parameters["adp_credentials"]["certificate"])
    key = make_key(parameters["adp_credentials"]["private_key"])
    select = queries.custom_select

    headers = {
        "user-agent": "cd-adpApi-func-python",
        "Authorization": f"Bearer {token['bearer_token']}",
        "accept": "application/json",
    }
    form_data = {
        "grant_type": "client_credentials",
        "client_id": parameters["adp_credentials"]["client_id"],
        "client_secret": parameters["adp_credentials"]["client_secret"],
    }
    params = {"$select": select}

    patch_requests(adapter=False)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    url = f"{endpoints.select_url}/{aoid}"

    # NOTE: This api call is sketchy, have to build in many retries
    try:
        r = session.get(
            url=url, headers=headers, params=params, cert=(cert, key), data=form_data
        )
        # try and get payload if no content attempt to call again 2nd attemps
        try:
            custom_worker = json.loads(r.content).get("workers")
            return(aoid, custom_worker)
        # if no payload make a third attempt but error out if unseccesful
        except json.JSONDecodeError as er:
            try:
                r = session.get(
                    url=url, headers=headers, params=params, cert=(cert, key), data=form_data,
                )
                custom_worker = json.loads(r.content).get("workers")
                return(aoid, custom_worker)
            except json.JSONDecodeError as er:
                r = session.get(
                    url=url, headers=headers, params=params, cert=(cert, key), data=form_data
                )
    # if SSL error attempt to get results again
    except SSLError as er:
        r = session.get(
            url=url, headers=headers, params=params, cert=(cert, key), data=form_data
        )
        properties = {"custom_dimensions": {"app": "ADP"}}
        logger.exception(
            f"Error in {__name__}, retrying request. \n\n\
            ERROR: {str(er)}. \n\n\
            TRACEBACK: {traceback.format_exc()}",
            extra=properties
        )
        # try to get content from the payload, if no content, try to request again
        try:
            custom_worker = json.loads(r.content).get("workers")
            return(aoid, custom_worker)
        except json.JSONDecodeError as er:
            r = session.get(
                url=url, headers=headers, params=params, cert=(cert, key), data=form_data
            )
            custom_worker = json.loads(r.content).get("workers")
            return (aoid, custom_worker)
