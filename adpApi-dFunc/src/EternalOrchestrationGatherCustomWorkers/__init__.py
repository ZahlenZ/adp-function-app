import azure.durable_functions as df
import contextlib

from datetime import datetime, timedelta

from SharedCode.LogIt import logger


def orchestrator_function(context: df.DurableOrchestrationContext) -> dict:
    """Orchestration that handles gathering all custom string attributes needed for workers

    Args:
        context (df.DurableOrchestrationContext): [parameters, token, workers]

    Returns:
        dict: workers
    """
    payload = context.get_input()

    if "new" not in payload:
        workers = []
        try:
            aoids = list(payload[2]["workers"]["associate_oid"].values())
        except ValueError as er:
            aoids = []
    else:
        try:
            aoids = payload[2]
        except Exception:
            aoids = []
        workers = payload[3]
        processed_worker = payload[4]
        with contextlib.suppress(Exception):
            workers.extend(processed_worker)

    if aoids:
        start = 0
        skip = 100
        parameters = payload[0]
        token = payload[1]

        worker_tasks = [
            context.call_activity("GetCustomAttributes", (parameters, token, aoid))
            for aoid in aoids[start : start + skip]
        ]

        processed_worker = yield context.task_all(worker_tasks)

        aoids = aoids[start + skip :]

        # NOTE: Can get rid of logging after this has run in production with no issues
        logger.func(f"Current Number of employees gather: {len(aoids)}")

        now = datetime.now().strftime("%H:%M:%S")
        token_time = datetime.strptime(
            parameters["token_time"], "%H:%M:%S"
        ) + timedelta(minutes=50)
        if now > token_time.strftime("%H:%M:%S"):
            token = yield context.call_activity("ADPOpenConnection", parameters)
            parameters["token_time"] = now

        context.continue_as_new(
            (parameters, token, aoids, workers, processed_worker, "new")
        )
    else:
        return workers


main = df.Orchestrator.create(orchestrator_function)
