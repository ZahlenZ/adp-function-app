import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext) -> dict:
    """Orchestration that handles gathering all base attributes of a worker

    Args:
        context (df.DurableOrchestrationContext): [parameters, token]

    Returns:
        dict: workers
    """
    payload = context.get_input()
    parameters = context.get_input()[0]
    token = context.get_input()[1]

    if "new" not in payload:
        workers = []
    else:
        workers = payload[2]
        if payload[3] is not None:
            workers.extend(payload[3])
        parameters["query"]["skip"] += 200
    while True:
        processed_workers = yield context.call_activity(
            "GetWorkerAttributes", (parameters, token)
        )
        if processed_workers["status"] == 204:
            break

        context.continue_as_new(
            (parameters, token, workers, processed_workers["workers"], "new")
        )

    return workers


main = df.Orchestrator.create(orchestrator_function)
