# Watashi

import json
import queue
from typing import Any, Dict, List, Optional


class EventBus:
    """
    Simple in-memory event bus (event queue simulation).
    Used to publish events like TICKET_CLASSIFIED.
    """

    def __init__(self, maxsize: int = 0):
        self._q: queue.Queue = queue.Queue(maxsize=maxsize)

    def publish(self, event: Dict[str, Any]) -> None:
        self._q.put(event)

    def consume(self, max_events: int = 100, block: bool = False, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        events = []
        for _ in range(max_events):
            try:
                evt = self._q.get(block=block, timeout=timeout)
                events.append(evt)
            except queue.Empty:
                break
        return events

    @staticmethod
    def to_json_line(event: Dict[str, Any]) -> str:
        return json.dumps(event, ensure_ascii=False)


# Global bus instance (simple for this project)
BUS = EventBus()
