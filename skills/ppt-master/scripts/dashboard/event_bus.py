#!/usr/bin/env python3
"""
PPT Master - Dashboard SSE Event Bus

Small in-process event bus for Server-Sent Events clients.

Usage:
    bus = EventBus()
    bus.publish("pipeline:state", state)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import json
import queue
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Iterator


def utc_now() -> str:
    """Return a current ISO timestamp."""
    return datetime.now(tz=timezone.utc).isoformat()


class EventBus:
    """SSE event fan-out with a bounded replay buffer."""

    def __init__(self, *, replay_limit: int = 200) -> None:
        self._lock = threading.Lock()
        self._next_id = 1
        self._clients: dict[int, queue.Queue] = {}
        self._events: deque[dict] = deque(maxlen=replay_limit)

    def publish(self, event_type: str, data: dict) -> dict:
        """Publish an event to connected clients and the replay buffer."""
        with self._lock:
            event = {
                "id": self._next_id,
                "event": event_type,
                "data": data,
            }
            self._next_id += 1
            self._events.append(event)
            clients = list(self._clients.items())
        for client_id, client_queue in clients:
            try:
                client_queue.put_nowait(event)
            except queue.Full:
                self.disconnect(client_id)
        return event

    def connect(self, *, last_event_id: int | None = None) -> tuple[int, queue.Queue, list[dict]]:
        """Register a client and return missed replay events."""
        client_queue: queue.Queue = queue.Queue(maxsize=100)
        with self._lock:
            client_id = self._next_id
            self._next_id += 1
            self._clients[client_id] = client_queue
            replay = [
                event for event in self._events
                if last_event_id is not None and event["id"] > last_event_id
            ]
        return client_id, client_queue, replay

    def disconnect(self, client_id: int) -> None:
        """Remove a client."""
        with self._lock:
            self._clients.pop(client_id, None)

    def client_count(self) -> int:
        """Return the number of connected clients."""
        with self._lock:
            return len(self._clients)


def encode_sse(event: dict) -> str:
    """Encode one event for ``text/event-stream``."""
    data = json.dumps(event["data"], ensure_ascii=False)
    return f"id: {event['id']}\nevent: {event['event']}\ndata: {data}\n\n"


def stream_events(
    bus: EventBus,
    client_id: int,
    client_queue: queue.Queue,
    replay: list[dict],
    *,
    heartbeat_seconds: int = 15,
) -> Iterator[str]:
    """Yield SSE chunks for one client."""
    try:
        for event in replay:
            yield encode_sse(event)
        last_heartbeat = time.time()
        while True:
            timeout = max(1, heartbeat_seconds - int(time.time() - last_heartbeat))
            try:
                event = client_queue.get(timeout=timeout)
                yield encode_sse(event)
            except queue.Empty:
                last_heartbeat = time.time()
                heartbeat = bus.publish(
                    "heartbeat",
                    {
                        "ts": utc_now(),
                        "uptime": None,
                        "clients": bus.client_count(),
                    },
                )
                yield encode_sse(heartbeat)
    finally:
        bus.disconnect(client_id)

