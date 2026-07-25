
from nodes.node_ingestion_bronze import read_from_gcs, validate_model, write_to_bronze, create_table

def run_ingestion():
    project_id = "project-27f747ae-dcc9-44b4-9f8"
    dataset = "devoteam_test"
    bucket_name = "devoteam_json"
    file_path = "rapport.json"
    
    create_table(project_id,dataset)
    raw_content = read_from_gcs(bucket_name, file_path)
    validated_logs = validate_model(raw_content)
    write_to_bronze(validated_logs, project_id, dataset, table="bronze_logs")
    #print(f"{len(validated_logs)} lignes ingérés dans la bronze")

if __name__ == "__main__":
    run_ingestion()