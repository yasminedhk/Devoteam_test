import pandas as pd
from utils.loader import read_gbq_table


#Fonction d'aggregation des données de la table silver pour produire un rapport gold 
def build_gold_report(silver_rows: list[dict]) -> dict:
    df = pd.DataFrame(silver_rows)

    insights = {
        "average_latency_ms": round(df["latency_ms"].mean(), 2),
        "max_cpu_usage": float(df["cpu_usage"].max()),
        "max_memory_usage": float(df["memory_usage"].max()),
        "error_rate": round(df["error_rate"].mean(), 4),
        "uptime_seconds": int(df["uptime_seconds"].max()),
    }

    anomalies_rows = df[df["has_anomaly"] == True]
    all_anomalies = []
    for _, row in anomalies_rows.iterrows():
        for desc in row["max_severity_descriptions"]:
            all_anomalies.append({
                "metric": None,  
                "value": None,
                "threshold": None,
                "severity": row["max_severity"],
                "description": desc,
            })

    # je garde uniquement medium/high (exclusion des "low") pour ne pas encombrer le rapport gold avec des anomalies low
    anomalies_for_llm = [a for a in all_anomalies if a["severity"] in ("medium", "high")]
    service_status_summary = {"online": [], "degraded": [], "offline": []}
    for service in ["database", "api_gateway", "cache"]:
        last_status = df[f"service_status_{service}"].iloc[-1]
        service_status_summary[last_status].append(service)

    return {
        "insights": insights,
        "anomalies": all_anomalies,
        "anomalies_for_llm": anomalies_for_llm,
        "service_status_summary": service_status_summary,
    }