
from google.cloud import storage
from google.cloud import bigquery
import json
import pandas as pd
import pandas as pd
import json
from models import model
from itertools import groupby

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

def create_table(project_id, dataset, sql_request):
    sql_request="sql/create_bronze_table.sql"

    client = bigquery.Client(project=project_id)              
    with open(sql_request, "r") as f:                             
        ddl = f.read().format(project_id=project_id, dataset=dataset)  
    client.query(ddl).result()
                                     
    print("Table Bronze vérifiée/créée.")

def validate_model(content):
    raw_logs=json.loads(content)
    if isinstance(raw_logs, dict):
        raw_logs = [raw_logs]
    return [model.LogEntry(**log) for log in raw_logs]

def write_to_bronze(logs,project_id, dataset, table ="bronze_logs"):
    if not logs:
        print("Aucun log")
        return
    client = bigquery.Client(project=project_id)

    rows_to_insert = [log.dict() for log in logs]
    rows_sorted = sorted(rows_to_insert, key=lambda r: r["timestamp"].date())

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


    for date_obj, group in groupby(rows_sorted, key=lambda r: r["timestamp"].date()):
        rows_for_date = list(group)

        for row in rows_for_date:
            row["timestamp"] = row["timestamp"].isoformat()

        partition_suffix = date_obj.strftime("%Y%m%d")
        table_with_partition = f"{project_id}.{dataset}.{table}${partition_suffix}"

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )

        job = client.load_table_from_json(
            rows_for_date,
            table_with_partition,
            job_config=job_config,
        )
        job.result()
        print(f"Partition _ {date_obj}_ ecrite : {len(rows_for_date)} ligne.")

    # def read_from_bronze_table(project_id, dataset, table="bronze_logs"):
    #     client = bigquery.Client(project=project_id)
    #     query = f"SELECT * FROM `{project_id}.{dataset}.{table}`"
    #     query_job = f"SELECT * FROM `{project_id}.{dataset}.{table}`"
    #     return client.query(query).result().to_dataframe()

   


