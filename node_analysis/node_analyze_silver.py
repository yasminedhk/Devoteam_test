import yaml
from google.cloud import bigquery
from utils.loader import write_partitions
from node_analysis.model import SilverLogEntry
import pandas as pd


"""
    Lecture de la table bronze=> enrichissement de la donnée => validation du modèle=> écriture brute dans la table silvers partitionnée par jours clusterisée par max_severity, has_anomaly
    """

SILVER_SCHEMA = [
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
    bigquery.SchemaField("has_anomaly", "BOOLEAN"),
    bigquery.SchemaField("max_severity", "STRING"),
    bigquery.SchemaField("max_severity_descriptions", "STRING", mode="REPEATED"),
    bigquery.SchemaField("service_status_database", "STRING"),
    bigquery.SchemaField("service_status_api_gateway", "STRING"),
    bigquery.SchemaField("service_status_cache", "STRING"),
]


def load_thereshold(path) -> dict:
    print(f"Loading thresholds from {path}...")
    with open(path, "r") as f:
        thereshold = yaml.safe_load(f)
        return thereshold

def get_severity(value, low, medium, high) -> str | None:
    if value >= high:
        return "high"
    elif value >= medium:
        return "medium"
    elif value >= low:
        return "low"
    return None

def get_service_severity(status, dict) -> str | None:
    return dict.get(status)

def detect_anomalies_for_log(log, thresholds) -> list[dict]:
    anomalies = []

    for metric, limits in thresholds["metrics"].items():
        value = log.get(metric)
        if value is None:
            continue

        severity = get_severity(value, limits["low"], limits["medium"], limits["high"])
        if severity:
            anomalies.append({
                "metric": metric,
                "value": value,
                "threshold": limits[severity],
                "severity": severity,
                "description": f"{metric} a atteint {value}, dépassant le seuil {severity} ({limits[severity]})."
            })

    service_status = log.get("service_status", {})
    for service_name, status in service_status.items():
        severity = get_service_severity(status, thresholds["service_status_severity"])
        if severity:
            anomalies.append({
                "metric": f"service_status.{service_name}",
                "value": None,
                "threshold": None,
                "severity": severity,
                "description": f"Le service {service_name} est en statut '{status}'."
            })

    return anomalies

#ajout d'une case has_anomalies pour indiquer si le log contient des anomalies
def has_anomaly(log, thresholds) -> bool:
    return len(detect_anomalies_for_log(log, thresholds)) > 0

#ajout d'une case max_severity qui sera utile pour l'analyse par prioriser les recommendations
def get_max_severity(log, thresholds) -> str | None:
    anomalies = detect_anomalies_for_log(log, thresholds)
    if not anomalies:
        return None

    severity_order = {"low": 1, "medium": 2, "high": 3}
    return max(anomalies, key=lambda a: severity_order[a["severity"]])["severity"]

#ajout d'une case max_severity_description pour donner toutes descriptions pour les plus grande anomalies
def get_max_severity_description(log, thresholds) -> str | None:
    anomalies = detect_anomalies_for_log(log, thresholds)
    if not anomalies:
        return None
    max_sev = get_max_severity(log, thresholds)
    return [a["description"] for a in anomalies if a["severity"] == max_sev]

#ajout des colonnes has_anomaly, max_severity, max_severity_description et flattening de service_status pour la table silver
def enrich_silver(logs,thersholds) -> pd.DataFrame:
    print(f"Enriching logs for silver table with thresholds: ...")
    
    df = pd.DataFrame(logs)
    # for idx, row in df.iterrows():
    #     log_dict = row.to_dict()
    #     print(type(log_dict["service_status"]), log_dict["service_status"])
    #     break 

    df["has_anomaly"] = df.apply(lambda row: has_anomaly(row.to_dict(), thersholds), axis=1)
    df["max_severity"] = df.apply(lambda row: get_max_severity(row.to_dict(), thersholds), axis=1)
    df["max_severity_descriptions"] = df.apply(
        lambda row: get_max_severity_description(row.to_dict(), thersholds), axis=1
    )

    df["service_status_database"] = df["service_status"].apply(lambda s: s["database"])
    df["service_status_api_gateway"] = df["service_status"].apply(lambda s: s["api_gateway"])
    df["service_status_cache"] = df["service_status"].apply(lambda s: s["cache"])

    df = df.drop(columns=["service_status"])
    [SilverLogEntry(**row) for row in df.to_dict(orient="records")]

    return df

def write_to_silver(df, project_id, dataset, table):
    """Écrit le DataFrame enrichi dans la table Silver."""
    rows = df.to_dict(orient="records")
    write_partitions(
        rows=rows,
        project_id=project_id,
        dataset=dataset,
        table=table,
        schema=SILVER_SCHEMA,
    )