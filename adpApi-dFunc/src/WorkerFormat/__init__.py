import pandas as pd

from flatten_json import flatten

from SharedCode.Config import columns
from SharedCode.Decorate import log_execution


@log_execution(func_name="WorkerFormat")
def main(WorkerFormat: list) -> dict:
    """Fully flattens JSON/Dictionary paylaod and renames columns

    Args:
        WorkerFormat (list): dict

    Returns:
        str: _description_
    """
    workers = WorkerFormat
    all_workers = []
    for worker in workers:
        flat_worker = flatten(worker)
        all_workers.append(flat_worker)

    workers_df = pd.DataFrame(all_workers)

    workers_df = workers_df.rename(columns=columns)
    columns_to_remove = workers_df.columns[workers_df.columns == "remove"]
    workers_df.drop(columns=columns_to_remove, inplace=True)

    workers_dict = workers_df.to_dict()

    return {"workers": workers_dict, "status": 200}
