from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class SilverLogEntry(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    disk_usage: float
    network_in_kbps: float
    network_out_kbps: float
    io_wait: float
    thread_count: int
    active_connections: int
    error_rate: float
    uptime_seconds: int
    temperature_celsius: float
    power_consumption_watts: float
    has_anomaly: bool
    max_severity: Literal["low", "medium", "high"] | None
    max_severity_descriptions: list[str]
    service_status_database: Literal["online", "degraded", "offline"]
    service_status_api_gateway: Literal["online", "degraded", "offline"]
    service_status_cache: Literal["online", "degraded", "offline"]