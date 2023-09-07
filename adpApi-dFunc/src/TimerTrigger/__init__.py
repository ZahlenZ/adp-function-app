import datetime
import logging

import azure.functions as func
import azure.durable_functions as df


async def main(mytimer: func.TimerRequest, starter: str) -> None:
    # sourcery skip: aware-datetime-for-utc
    utc_timestamp = (
        datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
    )

    client = df.DurableOrchestrationClient(starter)
    instance_id = await client.start_new("OrchestrationLoadBaseWorkers", None, None)

    logging.info("Python timer trigger function ran at %s", utc_timestamp)
