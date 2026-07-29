
from google.cloud import bigquery
from itertools import groupby


    
def create_table(project_id, dataset, sql_request,step):
    client = bigquery.Client(project=project_id)              
    with open(sql_request, "r") as f:                             
        ddl = f.read().format(project_id=project_id, dataset=dataset)  
    client.query(ddl).result()
                                     
    print(f"Table {step} existante ou créée.")

def write_partitions(rows, project_id, dataset, table, schema, timestamp="timestamp") :
    client = bigquery.Client(project=project_id)
    rows_sorted = sorted(rows, key=lambda r: r[timestamp].date())

    for date_obj, group in groupby(rows_sorted, key=lambda r: r[timestamp].date()):
        rows_for_date = list(group)
        for row in rows_for_date:
            row[timestamp] = row[timestamp].isoformat()

        partition_suffix = date_obj.strftime("%Y%m%d")
        table_ref = f"{project_id}.{dataset}.{table}${partition_suffix}"

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        job = client.load_table_from_json(rows_for_date, table_ref, job_config=job_config)
        job.result()
        print(f"Partition _ {date_obj}_ ecrite : {len(rows_for_date)} ligne.")

def read_gbq_table(project_id, dataset, table):
    client = bigquery.Client(project=project_id)
    query = f"SELECT * FROM `{project_id}.{dataset}.{table}`"
    return client.query(query).result().to_dataframe()

def count_rows(project_id, dataset, table) -> int:
    client = bigquery.Client(project=project_id)
    query = f"SELECT COUNT(*) AS nb_lignes FROM `{project_id}.{dataset}.{table}`"
    result = list(client.query(query).result())
    return result[0]["nb_lignes"]
    
