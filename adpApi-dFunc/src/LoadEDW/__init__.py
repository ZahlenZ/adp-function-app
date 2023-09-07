import numpy as np
import pandas as pd
import traceback

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from SharedCode.Decorate import log_execution
from SharedCode.LogIt import logger
from SharedCode.Patch import teams_notification


@log_execution(func_name="LoadEDW")
def main(LoadEDW: dict) -> dict:
    """Loads all workers into hr_stg_workers table in edw_stage

    Args:
        LoadEDW (dict): workers: {all workers}

    Returns:
        dict: {status: , worker_count}
    """
    edw_credentials = LoadEDW[0]["edw_credentials"]
    workers = LoadEDW[1]["workers"]
    workers_df = pd.DataFrame(workers)
    workers_df = workers_df.replace("NaN", None)

    user = edw_credentials["user"]
    password = edw_credentials["password"]
    host = edw_credentials["host"]
    db_name = edw_credentials["db_name"]
    driver = edw_credentials["driver"]

    connection_string = (
        f"Driver={driver};Server={host};Database={db_name};Uid={user};Pwd={password}"
    )
    connection_url = URL.create(
        "mssql+pyodbc", query={"odbc_connect": connection_string}
    )

    engine = create_engine(connection_url, fast_executemany=True, echo=False)
    Session = sessionmaker(bind=engine)
    try:
        with Session.begin():
            workers_df.to_sql(
                con=engine,
                schema="adp",
                name="stg_hr_workers",
                index=False,
                if_exists="append",
                chunksize=1000,
            )
        return {
            "status": 200,
            "worker_count": len(workers_df),
            "message": "All workers uploaded",
        }
    except Exception as er:
        properties = {"custom_dimensions": {"app": "ADP"}}
        logger.exception(
            f"Unknown error loading workers to Database. \n\n\
            ERROR: {str(er)}. \n\n\
            TRACEBACK: {traceback.format_exc()}",
            extra=properties
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params=LoadEDW[0])
        raise er
