
from nodes.node_ingestion_bronze import read_from_gcs, validate_model, write_to_bronze
from utils.loader import create_table,read_gbq_table
from config.config import PROJECT_ID, DATASET, BUCKET_NAME, FILE_PATH,BRONZE_TABLE
import argparse
from nodes.node_analyze_silver import enrich_silver,write_to_silver,load_thereshold

#Ingestion de données depuis GCS vers BigQuery dans la table bronze partitionnée par jours

def run_ingestion():
    create_table(PROJECT_ID,DATASET,sql_request="sql/create_bronze_table.sql",step="BRONZE")
    raw_content = read_from_gcs(BUCKET_NAME, FILE_PATH)
    validated_logs = validate_model(raw_content)
    write_to_bronze(validated_logs, PROJECT_ID, DATASET, table="bronze_logs")
    #print(f"{len(validated_logs)} lignes ingérés dans la bronze")

def run_analysis():
    create_table(PROJECT_ID,DATASET,sql_request="sql/create_silver_table.sql",step="SILVER")
    bronze_logs = read_gbq_table(project_id=PROJECT_ID, dataset=DATASET, table=BRONZE_TABLE)
    thereshold= load_thereshold(path="/Users/yasmine/devoteam/Devoteam_test/pipeline/config/thersholds.yaml")
    silver_df = enrich_silver(bronze_logs,thereshold)
    write_to_silver(silver_df, project_id=PROJECT_ID, dataset=DATASET,table="silver_logs")

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
    
    if args.step in ("analysis", "all"):
    #    thershold = load_thereshold(path="config/thersholds.yaml")
    #    print(f"Thresholds loaded: {thershold}")
        run_analysis()



    