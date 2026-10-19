# Athlete Readiness Sentinel - demo Oracle AIDP de bout en bout

Cette demo fictive montre comment Oracle AI Data Platform peut detecter des signaux precoces de fatigue ou de
rechute sans placer de score, de priorite ou de recommandation dans les donnees source.

## Parcours

```text
Object Storage raw
  -> notebook 01 Bronze - ingestion fidele + lineage
  -> notebook 02 Silver - typage + qualite + fenetres + label historique
  -> notebook 03 ML/MLOps - benchmark, calibration, metriques, run
  -> notebook 04 Gold - scoring, preuves, contexte agent
  -> AI Lakehouse SPORT_AGENT.SPORT_AGENT
  -> AIDP Agent Flow - SQL + RAG + explication + validation humaine
  -> cockpit web
```

## Ce qui est livre

- 42 rugbymen fictifs suivis sur 210 jours.
- 26 502 lignes de mesures structurees, dont un instantane nutritionnel pour les 42 joueurs.
- 72 evenements de blessure historiques, 1 191 declaratifs et 74 comptes rendus.
- 4 notebooks interactifs en formats `.py` lisible et `.ipynb` importable.
- Comparaison de Logistic Regression, Random Forest et Gradient Boosting, avec calibration.
- Champion local : **Régression logistique calibrée**, choisie sur la PR-AUC puis le score de Brier.
- Cockpit avec indice de vigilance à 7 jours, suivi GPS et nutritionnel, comparaison joueur/joueur ou période/période et dossier documentaire gouverné.
- Cockpit équipe enrichi avec dix KPI, analyses par poste, tableau des 42 joueurs et questions en langage naturel avec drill-down.
- Fiche joueur organisée en sous-onglets `Synthèse readiness`, `Données sources & documents` et `Comparer`.
- Entrée `Analyser avec l'agent` visible depuis la navigation, la fiche et l'indice individuel.
- Contrats Gold pour la connexion `SPORT_AGENT`, schema `SPORT_AGENT`.
- Brouillon d'Agent Flow avec SQL Tools, RAG Tool, Prompt Tools, garde-fous et ecriture humaine.
- Base de connaissance de 11 protocoles détaillés : charge, récupération, GPS, contacts, nutrition et gouvernance.
- Cockpit responsive aux couleurs sport et script de presentation.

Les metriques locales de controle sont produites par `validation/build_local_gold.py`. Elles servent a verifier
la coherence de la demo; le run AIDP reste la source de verite une fois les notebooks executes dans le workspace.

Sur le jeu fictif fourni, le champion obtient une ROC-AUC de 72,7%, une PR-AUC de 15,8% et un score de Brier
de 0,019. La ROC-AUC est une mesure de classement globale : elle ne doit pas etre comparee directement a
l'indice individuel d'un joueur. Par exemple, 29% est deja un niveau de vigilance eleve face au seuil de revue
de 9,4%.

## 1. Generer ou regenerer les sources

```bash
python3 data/generate_athlete_readiness_data.py
```

La seed est fixe. Le fichier `data/raw_object_storage_seed/manifest.json` confirme que les sources ne contiennent
ni score de risque ni recommandation.

## 2. Deposer le raw dans OCI Object Storage

Renseigner le bucket et le namespace, puis lancer :

```bash
export SPORT_BUCKET=<bucket>
export SPORT_NAMESPACE=<namespace>
export SPORT_PREFIX=athlete-readiness/raw
./scripts/upload_raw_to_object_storage.sh
```

Mettre ensuite les quatre URI `oci://` reelles dans `config/athlete_readiness_config.json`.
L'authentification Object Storage est implicite dans AIDP via l'identite IAM du workspace; aucune cle ne doit
etre placee dans les notebooks.

## 3. Preparer la connexion AI Lakehouse

Creer dans AIDP la connexion / external catalog `SPORT_AGENT`, puis le schema `SPORT_AGENT`. La configuration
suppose que le catalogue est adressable par :

```text
SPORT_AGENT.SPORT_AGENT.<TABLE>
```

Si l'identifiant interne du catalogue differe de son nom d'affichage, modifier uniquement
`ai_lakehouse.catalog_id` dans le fichier de configuration.

## 4. Importer et executer les notebooks

Copier la configuration vers :

```text
/Workspace/Config/athlete_readiness_config.json
```

Importer les notebooks dans `/Workspace/AthleteReadiness/`, puis les executer dans cet ordre :

1. `01_bronze_ingest.ipynb`
2. `02_silver_features.ipynb`
3. `03_ml_training_mlops.ipynb`
4. `04_gold_publish.ipynb`

Le notebook 03 utilise scikit-learn, joblib et mlflow. Si une bibliotheque n'est pas disponible sur l'image du
cluster, l'installer dans une cellule notebook avec `!pip install scikit-learn mlflow joblib`, puis redemarrer
uniquement le kernel du notebook. Ne jamais appeler `spark.stop()`.

Le manifeste logique `pipeline/athlete_readiness_job.json` donne l'ordre des taches pour creer ensuite le job AIDP.

## 5. Objets Gold publies

| Objet | Consommateur |
|---|---|
| `ATHLETE_READINESS_SCORES` | Reporting equipe et tendances |
| `ATHLETE_READINESS_HISTORY` | Comparaison joueur/joueur et periode/periode sur 90 jours |
| `ATHLETE_AGENT_CASES` | File de priorisation de l'agent |
| `ATHLETE_AGENT_CONTEXT` | Explication individuelle gouvernee |
| `ATHLETE_DOCUMENT_ACCESS` | Index gouverne des declaratifs, comptes rendus et blessures |
| `TEAM_READINESS_SUMMARY` | KPI globaux |
| `MODEL_PERFORMANCE` | Onglet MLOps |
| `MEDICAL_PROTOCOL_DOCUMENTS` | Source de la Knowledge Base |
| `AGENT_DECISION_LOG` | Contrat initial vide pour les decisions humaines |

Le script `sql/01_sport_agent_schema.sql` ajoute la table transactionnelle de validation et deux vues pratiques.

## 6. Construire l'Agent Flow

La collection AgentFlows de ce workspace a ete verifiee en lecture avec HTTP 200 le 8 septembre 2026. La definition
`agent_flow/athlete_readiness_agent_flow.json` reste volontairement en statut `READY_FOR_LIVE_BINDING` : il faut
encore lier le modele disponible, le compute IA, la Knowledge Base et l'endpoint ORDS avant validation/deploiement.

Ordre recommande dans le canvas :

```text
Message -> Guardrails -> Athlete Readiness Orchestrator
                         |- get_team_readiness_queue
                         |- get_athlete_readiness_context
                         |- get_model_performance
                         |- search_medical_protocols
                         |- explain_readiness_case
                         `- format_staff_plan

Le brouillon est ensuite retourné au cockpit. La validation humaine et l'appel
d'écriture ORDS sont gérés par le backend authentifié, hors du canvas Agent Flow.
```

Les instructions de securite se trouvent dans `agent_flow/orchestrator_instructions.md`.

Le cockpit utilise un endpoint agent unique avec deux portees explicites : `team` pour les questions sur l'effectif et `athlete` pour l'analyse detaillee d'un joueur. Les reponses globales conservent des liens de descente vers la fiche et l'analyse agent individuelles.

## 7. Ouvrir le cockpit

Version autonome : servir le repertoire `webapp/public` avec un serveur HTTP statique.

Version connectée à l'Agent Flow déployé. Cette URL est déjà la valeur par défaut
du runtime ; les variables ci-dessous permettent de la surcharger explicitement :

```bash
export AIDP_AGENT_CHAT_URL=https://gateway.aidp.eu-frankfurt-1.oci.oraclecloud.com/agentendpoint/a458e5a4-e35b-4a6e-88da-e3bcaa316ee0/chat
export AIDP_PAYLOAD_MODE=responses_api
uvicorn runtime.server:app --host 127.0.0.1 --port 8080
```

Puis ouvrir `http://127.0.0.1:8080`. Sans endpoint, le cockpit utilise sa simulation locale deterministe. Avec
l'endpoint, il conserve l'animation explicable puis remplace le brouillon par la reponse reelle du flux AIDP.

## Gouvernance

- Donnees fictives et pseudonymisation recommandee pour le POV.
- Vues Gold minimales selon le role.
- Aucun diagnostic et aucune autorisation de retour au jeu par l'agent.
- Validation medecin / preparateur obligatoire avant ecriture.
- Conservation du `model_run_id`, des preuves, des citations et du statut humain.

Created by Audrey Delou.
