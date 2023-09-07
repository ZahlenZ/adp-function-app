import traceback

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

from SharedCode.Decorate import log_execution
from SharedCode.LogIt import logger
from SharedCode.Patch import teams_notification


@log_execution(func_name="TruncateEDW")
def main(TruncateEDW: str) -> None:
    """Truncate hr_stg_workers table

    Args:
        TruncateEDW (dict): {adp_credentials, edw_credentials, query}

    Returns:
        None: None
    """
    edw_credentials = TruncateEDW["edw_credentials"]
    user = edw_credentials["user"]
    password = edw_credentials["password"]
    host = edw_credentials["host"]
    db_name = edw_credentials["db_name"]
    driver = edw_credentials["driver"]

    sql_statement = "TRUNCATE TABLE adp.stg_hr_workers"

    connection_string = (
        f"Driver={driver};Server={host};Database={db_name};Uid={user};Pwd={password}"
    )
    connection_url = URL.create(
        "mssql+pyodbc", query={"odbc_connect": connection_string}
    )
    engine = create_engine(connection_url, echo=False)
    Session = sessionmaker(bind=engine)

    try:
        with Session.begin() as session:
            session.execute(text(sql_statement))
    except Exception as er:
        logger.exception(
            f"Unknown error loading workers to Database. \n\n\
            ERROR: {str(er)}. \n\n\
            TRACEBACK: {traceback.format_exc()}"
        )
        payload = {"status": 500, "worker_count": None, "message": str(er)}
        teams_notification(status=payload, params=TruncateEDW)
        raise er

    return ""
