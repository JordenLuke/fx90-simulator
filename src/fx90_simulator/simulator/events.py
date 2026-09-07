import json
from datetime import datetime


def create_tag_event(event_number: int, tag_id: str) -> str:
    event = {
        "data": {
            "eventNum": event_number,
            "format": "epc",
            "idHex": tag_id,
        },
        "timestamp": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "type": "CUSTOM",
    }
    return json.dumps(event, separators=(",", ":"))
