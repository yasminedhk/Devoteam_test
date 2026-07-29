import yaml

def load_thereshold(path) -> dict:
    print(f"Loading thresholds from {path}...")
    with open(path, "r") as f:
        thereshold = yaml.safe_load(f)
        return thereshold

def get_severity(value, low_threshold, medium_threshold, high_threshold) -> str | None:
    if value >= high_threshold:
        return "high"
    elif value >= medium_threshold:
        return "medium"
    elif value >= low_threshold:
        return "low"
    return None


def get_service_severity(status, mapping) -> str | None:
    return mapping.get(status)

# Prends toutes les anomalies les low egalement 
def detect_anomalies_for_log(log, thresholds) -> list[dict]:
    anomalies = []

    for metric, bounds in thresholds["metrics"].items():
        value = log.get(metric)
        if value is None:
            continue

        severity = get_severity(value, bounds["low"], bounds["medium"], bounds["high"])
        if severity:
            anomalies.append({
                "metric": metric,
                "value": value,
                "threshold": bounds[severity],
                "severity": severity,
                "description": f"{metric} a atteint {value}, dépassant le seuil {severity} ({bounds[severity]})."
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


def compute_has_anomaly(log, thresholds) -> bool:
    return len(detect_anomalies_for_log(log, thresholds)) > 0


#POur determiner plus tard et isoler les anomalies medium et high
def get_max_severity(log, thresholds) -> str | None:
    anomalies = detect_anomalies_for_log(log, thresholds)
    if not anomalies:
        return None
    severity_order = {"low": 1, "medium": 2, "high": 3}
    return max(anomalies, key=lambda a: severity_order[a["severity"]])["severity"]


def get_max_severity_descriptions(log, thresholds) -> list[str]:
    anomalies = detect_anomalies_for_log(log, thresholds)
    if not anomalies:
        return []
    max_sev = get_max_severity(log, thresholds)
    return [a["description"] for a in anomalies if a["severity"] == max_sev]