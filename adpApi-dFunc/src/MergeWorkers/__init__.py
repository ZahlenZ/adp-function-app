import pandas as pd


def main(MergeWorkers: list) -> dict:
    """Merge the workers base attributes and the workers custom attributes into a single dataframe.

    Args:
        MergeWorkers (list): [workers, custom_workers]

    Returns:
        dict: workers with all attributes
    """
    workers = pd.DataFrame(MergeWorkers[0]["workers"])
    custom_workers = pd.DataFrame(MergeWorkers[1]["workers"])

    workers_df = pd.merge(
        workers, custom_workers, on="associate_oid", suffixes=("", "_delme")
    )
    

    return {"workers": workers_df.to_dict("records"), "status": 200}
