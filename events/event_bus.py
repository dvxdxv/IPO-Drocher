from collections import defaultdict
from typing import Callable, Dict, List, Type


class EventBus:
    def __init__(self):
        self._handlers: Dict[Type, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable):
        self._handlers[event_type].append(handler)

    def publish(self, event):
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            handler(event)