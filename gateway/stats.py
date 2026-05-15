from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StatsStore:
    total_requests: int = 0
    active_requests: int = 0
    latencies: deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    caller_counts: dict[str, int] = field(default_factory=dict)
    backend_health: dict[str, Any] = field(default_factory=lambda: {
        "status": "unknown",
        "last_checked": None,
        "last_error": None,
    })
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def request_started(self, client_ip: str) -> None:
        async with self._lock:
            self.total_requests += 1
            self.active_requests += 1
            self.caller_counts[client_ip] = self.caller_counts.get(client_ip, 0) + 1

    async def request_finished(self, elapsed_s: float) -> None:
        async with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.latencies.append(elapsed_s)

    async def update_health(self, status: str, error: str | None = None) -> None:
        async with self._lock:
            self.backend_health = {
                "status": status,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "last_error": error,
            }

    def compute_percentiles(self) -> dict[str, float | None]:
        if not self.latencies:
            return {"p50": None, "p95": None, "p99": None}
        sorted_ms = sorted(l * 1000 for l in self.latencies)
        n = len(sorted_ms)

        def pct(p: float) -> float:
            idx = int(p / 100 * n)
            return sorted_ms[min(idx, n - 1)]

        return {"p50": round(pct(50), 2), "p95": round(pct(95), 2), "p99": round(pct(99), 2)}

    def snapshot(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "latency_ms": self.compute_percentiles(),
            "callers": dict(self.caller_counts),
            "backend_health": dict(self.backend_health),
        }


stats = StatsStore()
