import json
import requests
import traceback

from requests.adapters import Retry
from requests.exceptions import SSLError

from SharedCode.Config import endpoints, queries
from SharedCode.KVAid import make_certificate, make_key
from SharedCode.Decorate import log_execution
from SharedCode.Patch import patch_requests, HTTPAdapter


@log_execution(func_name="CheckNoneWorkers")
def main(CheckNoneWorkers: list) -> list:
    """Attempts to find any workers that have None for their attributes and attempt a recall to adp

    Args:
        CheckNoneWorkers (list): (parameters, token, workers)

    Returns:
        list: workers with attributes
    """
    parameters = CheckNoneWorkers[0]
    token = CheckNoneWorkers[1]
    custom_workers = CheckNoneWorkers[2]
    cert = make_certificate(parameters["adp_credentials"]["certificate"])
    key = make_key(parameters["adp_credentials"]["private_key"])
    select = queries.custom_select
        
    headers = {
        "user-agent": "cd-adpapi-func-python",
        "Authorization": f"Bearer {token['bearer_token']}",
        "accept": "application/json",
    }
    form_data = {
        "grath_type": "client_credentials",
        "client_id": parameters["adp_credentials"]["client_id"],
        "client_secret": parameters["adp_credentials"]["client_secret"],
    }
    params = {"$select": select}
    
    patch_requests(adapter=False)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    
    none_type_workers = [
        aoid for aoid, attribute in dict(custom_workers).items() if attribute is None
    ]
    
    for i, j in enumerate(custom_workers):
        if j[0] in none_type_workers:
            aoid = j[0]
            url = f"{endpoints.select_url}/{aoid}"
            r = session.get(
                url=url, headers=headers, params=params, cert=(cert, key), data=form_data
            )
            try:
                custom_worker = json.loads(r.content).get("workers")
                custom_workers[i][1] = custom_worker
            except json.JSONDecodeError as er:
                r = session.get(
                    url=url, headers=headers, params=params, cert=(cert, key), data=form_data
                )
                custom_worker = json.loads(r.content).get("workers")
                custom_workers[i][1] = list(custom_worker)
            
    return custom_workers
