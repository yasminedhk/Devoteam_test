import pandas as pd
import json
import os
import uuid
from datetime import datetime, timezone
from google import genai
from node_gold_recommendation.anomaly_detect import detect_anomalies_for_log, load_thereshold
from node_gold_recommendation.prompt import PROMPT

"""
    Construction du rapport finale et génération de recommendation
"""



#pour chaque jours, toutes les anpmalies seront énuméres ainsi que les metrics comme spécifié dans les specs
def build_gold_rapports_by_day(silver_rows: list[dict]) -> list[dict]:
    df = pd.DataFrame(silver_rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date

    thresholds = load_thereshold("config/thersholds.yaml")
    rapports = []

    for rapport_date, day_df in df.groupby("date"):
        insights = {
            "average_latency_ms": round(day_df["latency_ms"].mean(), 2),
            "max_cpu_usage": float(day_df["cpu_usage"].max()),
            "max_memory_usage": float(day_df["memory_usage"].max()),
            "error_rate": round(day_df["error_rate"].mean(), 4),
            "uptime_seconds": int(day_df["uptime_seconds"].max()),
        }

        anomalies_rows = day_df[day_df["has_anomaly"] == True]
        all_anomalies = []
        for _, row in anomalies_rows.iterrows():
            log_dict = row.to_dict()
            # j'avais applatis les service_statut dans ma table parce que c'est une pratique recommandée sur gbq
            log_dict["service_status"] = {
                "database": log_dict.get("service_status_database"),
                "api_gateway": log_dict.get("service_status_api_gateway"),
                "cache": log_dict.get("service_status_cache"),
            }
            detailed = detect_anomalies_for_log(log_dict, thresholds)
            for a in detailed:
                a["timestamp"] = row["timestamp"].isoformat()
                all_anomalies.append(a)

        anomalies_for_llm = [a for a in all_anomalies if a["severity"] in ("medium", "high")]

        service_status_summary = {"online": [], "degraded": [], "offline": []}
        for service in ["database", "api_gateway", "cache"]:
            last_status = day_df[f"service_status_{service}"].iloc[-1]
            service_status_summary[last_status].append(service)

        rapports.append({
            "rapport_date": str(rapport_date),
            "insights": insights,
            "anomalies": all_anomalies,
            "anomalies_for_llm": anomalies_for_llm,
            "service_status_summary": service_status_summary,
        })

    return rapports


#appelle de l'api GEMINI pour recommander par jours pour les anomalies medium et high histoire de ne pas surcharger le modèle
def generate_recommendations(anomalies_for_llm, rapport_date) -> list[dict]:
    if not anomalies_for_llm:
        return []

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = PROMPT.format(
        rapport_date=rapport_date,
        anomalies_json=json.dumps(anomalies_for_llm, indent=2, default=str),
        nb_anomalies=len(anomalies_for_llm)
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    recommendations = json.loads(response.text)
    #Genaration d'id uniques pour chaque suggestions
    date = rapport_date.replace("-", "")
    for i, rec in enumerate(recommendations, start=1):
        rec["id"] = f"reco-{date}-{i:03d}" 
    
    return recommendations
 

#Consturction du JSON
def assemble_final_rapport(gold_rapport, recommendations) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "insights": gold_rapport["insights"],
        "anomalies": gold_rapport["anomalies"],
        "recommendations": recommendations,
        "service_status_summary": gold_rapport["service_status_summary"],
    }


#Boucle pour chaque jours pour établir un rapport
def run_recommendation_pipeline(silver_rows) -> list[dict]:
    daily_rapports = build_gold_rapports_by_day(silver_rows)

    final_rapports = []
    for rapport in daily_rapports:
        recommendations = generate_recommendations(
            rapport["anomalies_for_llm"],
            rapport["rapport_date"]
        )
        final_rapport = assemble_final_rapport(rapport, recommendations)
        final_rapports.append(final_rapport)
        print(f"[{rapport['rapport_date']}] {len(rapport['anomalies'])} anomalies, {len(recommendations)} recommandations.")

    return final_rapports

#Enregistrement du file 
def save_output(rapports, path = "output/output.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(rapports, f, indent=2, default=str,ensure_ascii=False)
    print(f"Rapports sauvegardés : {path}")