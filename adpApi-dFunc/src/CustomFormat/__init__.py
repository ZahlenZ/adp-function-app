import traceback

import pandas as pd

from flatten_json import flatten

from SharedCode.Config import custom_columns
from SharedCode.Decorate import log_execution
from SharedCode.LogIt import logger
from SharedCode.Patch import teams_notification


@log_execution(func_name="CustomFormat")
def main(CustomFormat: list) -> dict:
    """Format custom attributes in preperation for a merge with the base attributes

    Args:
        CustomFormat (list): workers

    Returns:
        dict: {workers, status}
    """
    custom_workers = CustomFormat[1]
    try:
        workers_data = [
            {**flatten(attribute[0]), "aoid": aoid}
            for aoid, attribute in dict(custom_workers).items()
        ]
        workers_df = pd.DataFrame(workers_data)
        workers_df = workers_df.rename(columns=custom_columns)
        columns_to_remove = workers_df.columns[workers_df.columns == "remove"]
        workers_df.drop(columns=columns_to_remove, inplace=True)
        workers_dict = workers_df.to_dict()
    except TypeError as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logger.exception(
            f"No attributes found for a worker in {__name__}.\n\n\
            ERROR: {str(er)}.\n\n\
            TRACEBACKE: {traceback.format_exc()}",
            extra=properties
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params=CustomFormat[0])
    return {"workers": workers_dict, "status": 200}
