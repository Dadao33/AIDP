# Installation and rehearsal

## Bound environment

Region: `eu-frankfurt-1`.
Workspace: `d05b6b48-22b4-4c5c-a7b6-737dc9be7362`.
Spark compute: `de8cff96-9784-41e5-9038-9ab6abe98bd8`.
AI compute: `690a6d05-55c1-4a33-9c2c-c7abdfcb6d1f`.
Object Storage namespace: `frn9volod3kr`; bucket: `AIDP_DATA`; dedicated prefix: `Demo_BIC/bic-retail-v1/`.

These are resource identifiers, not credentials. Use your own authenticated OCI profile with the necessary existing workspace and bucket permissions. Do not broaden access merely to make the demo run.

## Rebuild the data pipeline

1. Inspect `config/demo.json`. Use a fresh prefix if rebuilding in another environment.
2. Run `python3 scripts/upload_object_storage.py` to see the upload plan; add `--apply` to upload the five raw files and eight policy documents (as `.txt`). Existing objects are not overwritten. The current environment already contains all thirteen objects.
3. Put `config`, `shared`, `policies`, and the four notebooks under `/Workspace/BICDemo`. Keep relative paths. No secret is required inside a notebook.
4. Attach the supplied Spark compute. Execute notebooks 01 → 02 → 03 → 04. Each notebook reloads persisted inputs and does not require a shared interactive namespace.
5. Check the explicit completion messages and table counts. A notebook helper's wrapper status alone is not sufficient: inspect stderr and the final Gold-ready marker.
6. In MLOps inspect `BIC_Retail_Service_Risk`, chronological metrics and `model.json`. The deployable scoring contract is JSON weights plus `shared.engine.score`; this package does not claim a registered pyfunc endpoint.
7. The deployed job is `BIC_Retail_Daily.job`. `pipeline/create-job.verified.json` and `pipeline/update-job.verified.json` are the API payloads used successfully. The latter uses `dependsOn` objects, with one concurrent run and manual triggering. `job-plan.json` is the readable UI plan. No recurring schedule is needed for a fixed snapshot.

## Policy retrieval

The external volume `gold.bic_gold.bic_policy_docs` maps only the policy prefix. Knowledge Base `gold.bic_gold.kb_bic_b2b_policies` uses the embedding configuration available in this workspace. Confirm successful ingestion and retrieve FIN-01 before presenting RAG. The deterministic policy register remains authoritative for numerical checks; retrieval supplies the explanatory source text.

## Agent

`agent/instructions.md` and `agent/tools.json` contain all English configuration. The graph follows the workspace's CANVAS API. Use the verified create/update/deploy payloads shipped alongside the template, with your environment bindings. The API lifecycle is environment-dependent; read back the created flow and check the tool configuration before deployment.

The hosted BIC flow is separate from RetailNova and SPORT. Never reuse another demo's endpoint. Attach four read-only SQL tools to baseline BIC Gold facts and the policy retrieval tool to the BIC KB. Upload `agent/custom_tool_bic_live_calculations.zip` under `/Workspace/BICDemo/agent/` before deploying the four Custom Code tools. The package contains source inputs and model weights, never computed alternatives. After a new pipeline run, sync the cloud model, rebuild it with `python3 scripts/build_agent_tools.py`, upload the updated ZIP and redeploy the flow. Use the matching input snapshot in both the app and tools; receipt checks fail closed on a mismatch. The flow has no HTTP write tool. Test global exceptions, Carrefour facts, Monoprix policies and Monoprix after changing delay from 3 to 4.

## Local app and live mode

Python 3.9+ serves the app without web framework dependencies. NumPy is needed only for retraining. OCI CLI must be installed and authenticated for AIDP mode.

```bash
python3 scripts/sync_cloud_exports.py
bash scripts/start_aidp.sh
```

Set `OCI_CLI` if the executable is not on PATH, and `OCI_CONFIG_PROFILE` if not DEFAULT. For rehearsal: `BIC_MODE=rehearsal python3 runtime/server.py --port 8766`.

The app listens only on 127.0.0.1 and checks browser origin. Do not expose this demonstration server publicly. Live API failures are shown; there is no automatic substitution with a rehearsal response. The decisions file is created locally under `.runtime/`; this is a rehearsal store, not enterprise workflow persistence.

## Before a meeting

Warm both computes, sync the exact cloud export, test one question, reset the view, open the AIDP notebooks and flow, and open the PowerPoint. Avoid model training during the live presentation. See the French guide for the timed sequence and fallback wording.
