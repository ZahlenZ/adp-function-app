import azure.durable_functions as df

from SharedCode.Patch import teams_notification


def orchestrator_function(context: df.DurableOrchestrationContext):
    """This orchestration will load all the base attributes of workers into the EDW as well as adding messages to a queue for a listener that will pick up and load the custom attributes."""

    parameters = yield context.call_activity("Parameters")

    token = yield context.call_activity("ADPOpenConnection", parameters)

    workers = yield context.call_sub_orchestrator(
        "EternalOrchestrationGatherBaseWorkers", (parameters, token)
    )

    workers = yield context.call_activity("WorkerFormat", workers)

    custom_workers = yield context.call_sub_orchestrator(
        "EternalOrchestrationGatherCustomWorkers", (parameters, token, workers)
    )

    token = yield context.call_activity("ADPOpenConnection", parameters)

    custom_workers = yield context.call_activity(
        "CheckNoneWorkers", (parameters, token, custom_workers)
    )

    custom_workers = yield context.call_activity("CustomFormat", (parameters, custom_workers))

    workers = yield context.call_activity("MergeWorkers", (workers, custom_workers))

    yield context.call_activity("TruncateEDW", parameters)

    payload = yield context.call_activity("LoadEDW", (parameters, workers))

    teams_notification(status=payload, params=parameters)


main = df.Orchestrator.create(orchestrator_function)
