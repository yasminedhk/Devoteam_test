CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.silver_logs` (
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
  has_anomaly BOOLEAN,
  max_severity STRING,
  max_severity_descriptions ARRAY<STRING>,
  service_status_database STRING,
  service_status_api_gateway STRING,
  service_status_cache STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY has_anomaly, max_severity;