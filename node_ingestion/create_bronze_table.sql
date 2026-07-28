CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.bronze_logs` (
  timestamp TIMESTAMP NOT NULL,
  cpu_usage FLOAT64,
  memory_usage FLOAT64,
  latency_ms FLOAT64,
  disk_usage FLOAT64,
  network_in_kbps FLOAT64,
  network_out_kbps FLOAT64,
  io_wait FLOAT64,
  thread_count INT64,
  active_connections INT64,
  error_rate FLOAT64,
  uptime_seconds INT64,
  temperature_celsius FLOAT64,
  power_consumption_watts FLOAT64,
  service_status STRUCT <
    database STRING,
    api_gateway STRING,
    cache STRING
  >
)
PARTITION BY DATE(timestamp);
