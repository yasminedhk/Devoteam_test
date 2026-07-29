from pydantic import BaseModel
from datetime import datetime
from typing import Literal

"""Pour valider le modele de donnée et les variables avant ingestion et detecter les lignes anormales
"""
class ServiceStatus(BaseModel):
    database: Literal["online", "degraded", "offline"]
    api_gateway: Literal["online", "degraded", "offline"]
    cache: Literal["online", "degraded", "offline"]

class LogEntry(BaseModel):
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
    service_status: ServiceStatus