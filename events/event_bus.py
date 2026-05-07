# events/event_bus.py

import logging
from collections import defaultdict
from typing import Callable, Dict, List, Type, Any


logger = logging.getLogger("ipo_drocher.event_bus")


class EventBus:
    def __init__(self):
        self._handlers: Dict[Type, List[Callable]] = defaultdict(list)
        self._last_event: Any = None

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        """
        Register event handler.
        """

        handler_name = self._get_handler_name(handler)

        logger.info(
            "SUBSCRIBE | event=%s | handler=%s",
            event_type.__name__,
            handler_name,
        )

        self._handlers[event_type].append(handler)

    def publish(
        self,
        event,
        publisher: str = "unknown",
        metadata: dict | None = None,
    ):
        """
        Publish event to all subscribers.
        """

        event_type = type(event)
        event_name = event_type.__name__

        handlers = self._handlers.get(event_type, [])

        logger.info(
            "PUBLISH | event=%s | publisher=%s | subscribers=%s | metadata=%s | payload=%s",
            event_name,
            publisher,
            [self._get_handler_name(h) for h in handlers],
            metadata or {},
            event,
        )

        if not handlers:
            logger.warning(
                "NO_SUBSCRIBERS | event=%s | publisher=%s",
                event_name,
                publisher,
            )
            return None

        result = None

        for handler in handlers:
            handler_name = self._get_handler_name(handler)

            logger.info(
                "HANDLE_START | event=%s | handler=%s",
                event_name,
                handler_name,
            )

            try:
                result = handler(event)

                logger.info(
                    "HANDLE_DONE | event=%s | handler=%s | result=%s",
                    event_name,
                    handler_name,
                    result,
                )

            except Exception as exc:
                logger.exception(
                    "HANDLE_ERROR | event=%s | handler=%s | error=%s",
                    event_name,
                    handler_name,
                    exc,
                )
                raise

        self._last_event = event

        return result

    @staticmethod
    def _get_handler_name(handler: Callable) -> str:
        """
        Return readable handler name.
        """

        owner = getattr(handler, "__self__", None)

        if owner:
            return f"{owner.__class__.__name__}.{handler.__name__}"

        return getattr(handler, "__name__", str(handler))