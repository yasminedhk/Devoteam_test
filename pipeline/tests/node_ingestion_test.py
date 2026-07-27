import json
from nodes.node_ingestion_bronze import validate_model

#valider qu'on ne perd pas de logs lors de l'ingestion
def test_validate_logs_count():
    
    with open("data/rapport.json", "r") as f:
        raw_content = f.read()
    
    raw_json = json.loads(raw_content)
    expected_count = len(raw_json) if isinstance(raw_json, list) else 1
    
    logs = validate_model(raw_content)
    
    assert len(logs) == expected_count
    print(f"{len(logs)} logs insérés , expected {expected_count}.")

#Pas de doublons pour la data quality
def test_no_duplicate_timestamps_in_source():
    with open("data/rapport.json", "r") as f:
        raw_content = f.read()

    logs = validate_model(raw_content)
    timestamps = [log.timestamp for log in logs]

    assert len(timestamps) == len(set(timestamps)), (
        f"Doublons détectés : {len(timestamps)} , {len(set(timestamps))} timestamps uniques."
    )