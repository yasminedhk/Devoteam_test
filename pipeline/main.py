
from nodes.node_ingestion_bronze import read_from_gcs, validate_model, write_to_bronze, create_table
from config.config import PROJECT_ID, DATASET, BUCKET_NAME, FILE_PATH
import argparse

#Ingestion de données depuis GCS vers BigQuery dans la table bronze partitionnée par jours

def run_ingestion():
    create_table(PROJECT_ID,DATASET,sql_request="sql/create_bronze_table.sql")
    raw_content = read_from_gcs(BUCKET_NAME, FILE_PATH)
    validated_logs = validate_model(raw_content)
    write_to_bronze(validated_logs, PROJECT_ID, DATASET, table="bronze_logs")
    #print(f"{len(validated_logs)} lignes ingérés dans la bronze")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        choices=["ingestion", "analysis", "recommendation", "all"],
        default="all"
    )
    args = parser.parse_args()

    if args.step in ("ingestion", "all"):
        run_ingestion()

    