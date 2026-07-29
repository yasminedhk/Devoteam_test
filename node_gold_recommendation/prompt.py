
PROMPT = """Tu es un ingénieur SRE (Site Reliability Engineer) expérimenté. Voici la liste complète des anomalies détectées le {rapport_date} sur un système de monitoring d'infrastructure :

{anomalies_json}

IMPORTANT : Tu dois traiter TOUTES les anomalies listées ci-dessus, sans exception. Il y a {nb_anomalies} anomalies au total. Si plusieurs anomalies sont clairement liées entre elles, tu peux les regrouper dans une seule recommandation.

Le champ "target" de chaque recommandation doit correspondre exactement au "metric" de l'anomalie concernée.

Réponds UNIQUEMENT avec un JSON valide, structuré comme ceci :
[
  {{
    "id": "reco-1",
    "action": "description de l'action à mener",
    "target": "nom_de_la_metric_concernee",
    "parameters": {{}},
    "benefit_estimate": "bénéfice attendu en langage clair"
  }}
]
"""