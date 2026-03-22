"""AWS Lambda: S3 ObjectCreated -> Celery process_image task via Redis/Kombu."""

import os
import re

from kombu import Connection
from kombu.utils.uuid import uuid

BROKER_URL = os.environ["CELERY_BROKER_URL"]
RAW_PATTERN = re.compile(r"^raw/(foods|drinks)/([A-Z0-9]{26})/.+\..+$")

TASK_MAP = {
    "foods": "modules.foods.tasks.process_food_image",
    "drinks": "modules.drinks.tasks.process_drink_image",
}


def handler(event, context):
    detail = event.get("detail", {})
    key = detail.get("object", {}).get("key")

    if not key:
        return {"status": "skipped", "reason": "no key"}

    match = RAW_PATTERN.match(key)
    if not match:
        return {"status": "skipped", "key": key}

    entity_type = match.group(1)
    entity_id = match.group(2)

    task_name = TASK_MAP.get(entity_type)
    if task_name is None:
        return {"status": "skipped", "reason": f"unknown entity type: {entity_type}"}

    with Connection(BROKER_URL) as conn:
        with conn.SimpleQueue("celery") as queue:
            task_id = uuid()
            queue.put(
                [
                    [entity_id, key],
                    {},
                    {"callbacks": None, "errbacks": None, "chain": None, "chord": None},
                ],
                headers={
                    "lang": "py",
                    "task": task_name,
                    "id": task_id,
                    "shadow": None,
                    "eta": None,
                    "expires": None,
                    "group": None,
                    "group_index": None,
                    "retries": 0,
                    "timelimit": [None, None],
                    "root_id": task_id,
                    "parent_id": None,
                    "argsrepr": repr((entity_id, key)),
                    "kwargsrepr": "{}",
                    "origin": "lambda",
                    "ignore_result": True,
                },
                content_type="application/json",
                content_encoding="utf-8",
            )

    return {"status": "dispatched", "entity_type": entity_type, "entity_id": entity_id}
