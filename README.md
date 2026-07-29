# Optimisation de l’Infrastructure Technique pour Jean
(CTO)

## Introduction: 
Ce repo contient une proposition d'architecture modulaire pour la détection et la suggestion de correction d'anomalies, grace à l'IA générative pour des logs SRE

## Sommaire : 
- Architecture générale et structure du projet 
- Ingestion des données à partir d'un fichiers de logs json
- Détection d'anomalies
- Génération de recommendations
- justification des choix techniques
- Pistes d'évolutions
- Documentation

  ## Architecture générale et structure du projet 
  Le pipeline utilise l'architecture médaillon , organisée dans des noeuds indépendants et exécutable séparément en lançant le main, suivi de --step (analysis, ingestion, recommendation)
  Ce qui permet d'isoler les étapes et faciliter le débogguing sans rejouer l'intégralité du pipeline

  ```
  bash
  python main.py --step ingestion
  python main.py --step analysis
  python main.py --step recommendation
  python main.py --step all
  ```
  Structure du projet : 
  _main.py
  _requirements.txt 
  _.env 
  _.gitignore
  config:
    _thersolds.yaml
  data: 
    _rapport.json
  node_analysis:
    _create_silver_table.sql
    _model.py
    _node_analyse_silver.py
    _node_silver_test.py
  node_ingestion:
    _create_bronze_table.sql
    _model.py
    _node_bronze_silver.py
    _node_bronze_test.py
  node_gold_recommendation:
    _anomaly_detect
    _node_gold_recommendation.p
    _prompt.py
  utils:
   _ loader.py
    
  
## Ingestion des données à partir d'un fichiers de logs json (node_ingestion)
**BUT** : Ingérer les données json chargée dans cloud storage sur GBQ et partitionner par Date
Le fichier JSON est lu depuis Google Cloud Storage, puis chaque entrée est validée via un modèle Pydantic (présence des champs obligatoires, bon types). Aucune Transformation n'est appliquée à ce stade : la table Bronze reste fidèle à la donnée source, afin de faciliter la détection d'anomalies dans la data et la possibilité, revenir un step en arrière si anomalies lors des transformations sans passer pour une nouvelles ingestion, et garder 'un historique'.

Les données validées sont ensuite écrites dans la table BigQuery `bronze_logs`, avec un mécanisme d'override par partition (`WRITE_TRUNCATE` + decorator `$YYYYMMDD`) garantissant l'idempotence en cas de relance du script sur un même fichier.
Des tests pytests sont ensuite réalisé pour ne pas s'assurer de perte de lignes 


## Détection d'Anomalies

**BUT** :entamer les premieres modifications et  identifier des metrics  anormales 

La détection d'anomalies se fait statistiquement au lieu d'avoir recours à un LLM, car la détection d'anomalies nécessite de la précision. La réponse d'un LLM dépend de plusieurs facteurs (choix du modèle, prompt)
Du coup, un même log pourrait être classé différemment selon le LLM choisi ce qui n'est pas recommandé pour du monitoring et la détection d'alertes.

Deux logiques de détection distinctes sont appliquées, conciliée dans le fichier thersholds, une pour les métrics numériques l'autre pour les métrics statuts service.
Pour la distinction entre medium et low je me suis basée sur un quantile de 75% au lieu de 90% car la valeur était beaucoup trop proche. 

Des colonnes ont été ajoutées à silver : 
- `has_anomaly` (booléen) : au moins une anomalie détectée sur ce log
- `max_severity` : la sévérité la plus élevée détectée sur ce log
- `max_severity_descriptions` : description.s textuelle.s de la ou des anomalie.s à cette sévérité maximale
- Statuts de service aplatis (`service_status_database`, `service_status_api_gateway`, `service_status_cache`)
La partion se fait sur has_anomly et max_severity pour une optimisation de cout et célérité de la requête

## Génération de Recommandations

**Objectif** : production d'un rapport output.json, pour chaque jours, résumer les metrics, énumérer les anomalies détectées et pour les anomalies medium et high générer des suggestions 

```json
{
  "timestamp": "string (ISO 8601)",
  "insights": {
    "average_latency_ms": "number",
    "max_cpu_usage": "number",
    "max_memory_usage": "number",
    "error_rate": "number",
    "uptime_seconds": "number"
  },
  "anomalies": [
    {
      "metric": "string",
      "value": "number",
      "threshold": "number",
      "severity": "string (low|medium|high)",
      "description": "string"
    }
  ],
  "recommendations": [
    {
      "id": "string",
      "action": "string",
      "target": "string",
      "parameters": "object",
      "benefit_estimate": "string"
    }
  ],
  "service_status_summary": {
    "online": ["string"],
    "degraded": ["string"],
    "offline": ["string"]
  }
}
```

Plutot que de faire appel au LLM ligne par ligne pour chaque anomalie détecter, on les envoies par paquet en un seul call API GEMINI. Cette approche limite le nombre d'appels (coût, quota) et surtout permet au modèle de détecter des corrélations entre anomalies survenant simultanément

Pour le prompt on sépecifie le role du LLM (ingénieures-conseils SRE) cohérent avec le référentiel Golden Signals fournit dans la doc 

## Choix techniques et justifications

GCP a été choisi pour deux raisons principales : la possibilité de faire évoluer l'architecture facilement (Cloud Functions et scheduler , Cloud Composer (airflow) , data Studio s'intègrent nativement), et la possibilité de requêter les données facilement via SQL, avec un onglet de visualisation intégré à la Console BigQuery. 

### Architecture medallion (Bronze / Silver / Gold)
Ce découpage permet de bien séparer les noeuds facilitant ainsi le travail collaboratif, et puis reprendre le pipeline en cas d'anomalies à l'étapes précédent sans nécessairement tout recommencer (ingestions ....). Les transformations sont appliquées dans la table silver, pour la table gold (non mise en place), je verrais plus une agrégation par jours pour la construction de rapports journaliers.

## Pistes d'évolution
- **Déploiement de cloud functions**: utiliser des Cloud Functions déclenchées automatiquement lors du dépôt d'un fichier sur Cloud Storage ou de l'ajout de nouvelles lignes, paramétrables via Cloud Scheduler, ou orchestrées via Airflow/Cloud Composer selon la taille du projet, pour une meilleure visualisation des étapes du pipeline
- **Orchestration des transformations via dbt** : remplacer la chaîne pandas/Pydantic/pytest par des modèles dbt pour la partie transformation SQL (Bronze → Silver → Gold), avec tests déclaratifs et le data lineage 
- **Bucket de rapports** : transmission automatisée des rapports générés chaque jour vers un bucket
- **Table Gold sans recommandations** : écriture d'une table Gold sans le texte des recommandations (présents dans les rapports quotidiens sur GCS), afin de permettre une visualisation des rapports quotidiens dans un outil de BI comme Looker Studio, connecté directement à BigQuery
- **Déploiement d'une applications** : selon le besoin client, déployer une application Streamlit affichant les métriques, anomalies et suggestions de chaque jour de façon interactive.

## Documentations
```
- https://www.linkedin.com/advice/1/how-can-you-use-r-identify-outliers-anomalies-your-smfsf?lang=fr
- https://medium.com/@srikrishnan.tech/llms-are-not-anomaly-detectors-and-that-s-a-good-thing-7e0272f62a7c#
- https://sre.google/sre-book/monitoring-distributed-systems/#xref_monitoring_golden-signals
```



