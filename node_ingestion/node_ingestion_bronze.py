
from google.cloud import storage
from google.cloud import bigquery
import json
import pandas as pd
import pandas as pd
import json
from node_ingestion.model_bronze import LogEntry
from itertools import groupby
from utils.loader import write_partitions

"""
    Lecture du json file de storage=> validation du modèle=> écriture brute dans la table bronze partitionnée par jours
    """

project_id = "project-27f747ae-dcc9-44b4-9f8"

def read_from_gcs(bucket_name, file_path) -> str:
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    content = blob.download_as_text()
    #print(content)
    return content

def validate_model(content):
    
    raw_logs=json.loads(content)
    if isinstance(raw_logs, dict):
        raw_logs = [raw_logs]
    return [LogEntry(**log) for log in raw_logs]

def write_to_bronze(logs,project_id, dataset, table ="bronze_logs"):
    if not logs:
        print("Aucun log")
        return
    rows_to_insert = [log.dict() for log in logs]
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("cpu_usage", "FLOAT64"),
        bigquery.SchemaField("memory_usage", "FLOAT64"),
        bigquery.SchemaField("latency_ms", "FLOAT64"),
        bigquery.SchemaField("disk_usage", "FLOAT64"),
        bigquery.SchemaField("network_in_kbps", "FLOAT64"),
        bigquery.SchemaField("network_out_kbps", "FLOAT64"),
        bigquery.SchemaField("io_wait", "FLOAT64"),
        bigquery.SchemaField("thread_count", "INT64"),
        bigquery.SchemaField("active_connections", "INT64"),
        bigquery.SchemaField("error_rate", "FLOAT64"),
        bigquery.SchemaField("uptime_seconds", "INT64"),
        bigquery.SchemaField("temperature_celsius", "FLOAT64"),
        bigquery.SchemaField("power_consumption_watts", "FLOAT64"),
        bigquery.SchemaField("service_status", "RECORD", mode="NULLABLE", fields=[
            bigquery.SchemaField("database", "STRING"),
            bigquery.SchemaField("api_gateway", "STRING"),
            bigquery.SchemaField("cache", "STRING"),
        ]),
    ]
    write_partitions(
        rows=rows_to_insert,
        project_id=project_id,
        dataset=dataset,
        table=table,
        schema=schema,
        timestamp="timestamp"
    )


    

 

   


