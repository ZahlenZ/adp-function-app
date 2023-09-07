import asyncio
import time
import traceback
from functools import wraps

from SharedCode.LogIt import logger


def retry(max_tries=5, delay_seconds=1.5):
    """retry a function up to max_tries with a delay between tries of delay_seconds

    Args:
        max_tries (int, optional): how many retries to attempt. Defaults to 5.
        delay_seconds (float, optional): how many seconds between attempts. Defaults to 1.5.
    """

    def decorator_retry(func):
        @wraps(func)
        def wrapper_retry(*args, **kwargs):
            tries = 1
            while tries < max_tries:
                try:
                    module_name = kwargs.get("module_name", "None")
                    if tries > 1:
                        logger.warning(
                            f"HTTP Request from {module_name}: attempt number {tries}."
                        )
                    return func(*args, **kwargs)
                except Exception as er:
                    logger.warning("Starting new retry attempt")
                    logger.warning(f"{str(er)}")
                    tries += 1
                    if tries == max_tries:
                        logger.critical(
                            f"Reached max retry attempts.\n\n\
                            ERROR: {str(er)}.\n\n\
                            TRACEBACK: {traceback.format_exc()}"
                        )
                        raise er
                    time.sleep(delay_seconds)

        return wrapper_retry

    return decorator_retry


def log_execution(_func=None, *, func_name=__name__):
    """Log the start and end of an activity function.

    Args:
        _func (_type_, optional): The function being wrapped. Defaults to None.
        func_name (_type_, optional): Adds the name of the function to the logs. Defaults to __name__.
    """

    def log_func(func):
        @wraps(func)
        def wrapper_log_func(*args, **kwargs):
            try:
                properties = {"custom_dimensions": {"app": "ADP"}}
                logger.func(f"Running: {func_name}", extra=properties)
                if asyncio.iscoroutinefunction(func):
                    # convert the coroutine object to a regular function
                    result = asyncio.run(func(*args, **kwargs))
                else:
                    result = func(*args, **kwargs)
            except Exception as er:
                properties = {"custom_dimensions": {"app": "ADP"}}
                logger.exception(
                    f"EXCEPTION Raised in {func_name}. \n\n\
                    ERROR: {str(er)}.\n\n\
                    TRACEBACK: {traceback.format_exc()}",
                    extra=properties
                )
            else:
                logger.func(f"Successfully Executed: {func_name}")
                return result

        return wrapper_log_func

    return log_func if _func is None else log_func(_func)
