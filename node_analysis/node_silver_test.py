from utils.loader import count_rows
from google.cloud import bigquery
from dotenv import load_dotenv
import os 

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")
BUCKET_NAME = os.getenv("BUCKET_NAME")
FILE_PATH = os.getenv("FILE_PATH") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BRONZE_TABLE = os.getenv("BRONZE_TABLE")
SILVER_TABLE= os.getenv("SILVER_TABLE")
"""
Tests pour m'assurer de la Data quality et m'assurer qu'il n'ai pas de pertes de logs ni d'incohérence dans la data
"""

#perte de data entre bronze et silver
def test_silver_row_count_matches_bronze():
    bronze_count = count_rows(PROJECT_ID, DATASET, BRONZE_TABLE)
    silver_count = count_rows(PROJECT_ID, DATASET, SILVER_TABLE)
    assert bronze_count == silver_count

#cohérence des données max_severity et has_anomaly
def test_anomaly_and_severity_consistency():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT COUNT(*) AS inconsistent_count
        FROM `{PROJECT_ID}.{DATASET}.{SILVER_TABLE}`
        WHERE (max_severity IS NULL AND has_anomaly = TRUE)
           OR (max_severity IS NOT NULL AND has_anomaly = FALSE)
    """
    result = list(client.query(query).result())
    inconsistent_count = result[0]["inconsistent_count"]
    assert inconsistent_count == 0, f"Resultat: {inconsistent_count} anomalies."

def test_max_severity_valid_values():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT COUNT(*) AS inconsistent_count
        FROM `{PROJECT_ID}.{DATASET}.{SILVER_TABLE}`
        WHERE (max_severity IS NOT NULL AND max_severity NOT IN ('low', 'medium', 'high'))
    """
    result = list(client.query(query).result())
    inconsistent_count = result[0]["inconsistent_count"]
    assert inconsistent_count == 0, f"Resultat: {inconsistent_count} anomalies."

def test_service_status_valid_values():
    client = bigquery.Client(project=PROJECT_ID)
    query = f"""
        SELECT COUNT(*) AS inconsistent_count
        FROM `{PROJECT_ID}.{DATASET}.{SILVER_TABLE}`
        WHERE service_status_database NOT IN ('online', 'degraded', 'offline')
        OR service_status_api_gateway NOT IN ('online', 'degraded', 'offline')
        OR service_status_cache NOT IN ('online', 'degraded', 'offline')
    """
    result = list(client.query(query).result())
    inconsistent_count = result[0]["inconsistent_count"]
    assert inconsistent_count == 0, f"Resultat: {inconsistent_count} anomalies."
