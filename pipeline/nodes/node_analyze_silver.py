import yaml

def load_thereshold(path="config/thresholds.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)