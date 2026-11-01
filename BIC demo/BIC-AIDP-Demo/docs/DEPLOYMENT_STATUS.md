# Deployment status — 31 October 2026

## Verified and running

| Component | Resource / result |
|---|---|
| Region | `eu-frankfurt-1` |
| Workspace | `d05b6b48-22b4-4c5c-a7b6-737dc9be7362` |
| Workspace folder | `/Workspace/BICDemo` |
| Spark compute | `Data_Eng_Cluster` — `de8cff96-9784-41e5-9038-9ab6abe98bd8` |
| AI compute | `690a6d05-55c1-4a33-9c2c-c7abdfcb6d1f` |
| Source data | `oci://AIDP_DATA@frn9volod3kr/Demo_BIC/bic-retail-v1/` |
| Uploaded sources | Five raw files and eight policy documents |
| Published scope | 26 baseline accounts; scenarios and alternatives calculated on demand |
| Data pipeline | `BIC_Retail_Daily.job` — `024588ff-d9f5-48d6-90e7-355874702db1` |
| Pipeline execution | `8179770f-784c-45fd-a109-50ddd85dcb78` — **SUCCESS**, 30 October 2026, 14:55–14:59 UTC (previous baseline build; notebook 04 updated on 31 October) |
| MLflow experiment | `BIC_Retail_Service_Risk` |
| Latest verified MLflow run | `07fa9eb8d3e84880a2553261d2e8bc1b` |
| Agent | `BIC_Retail_Service_Copilot` — `6273a6c2-4e07-4e40-ab24-8a44c9475f69` |
| Hosted deployment | `cbeecf67-5492-4aaf-83d8-5ec58775b97f` — **ACTIVE** |
| Agent tools | Four Custom Code calculators, four read-only SQL tools and policy retrieval |
| Knowledge Base | `gold.bic_gold.kb_bic_b2b_policies` |
| KB source ingestion | `a7244f6c722e4eda8fb9deb8c4df604f` — **SUCCEEDED**, 8 records added |
| Local/cloud consistency | All 26 baseline scenario hashes matched the exported cloud model |
| Local application | `http://127.0.0.1:8766/` — AIDP agent mode |

Agent endpoint:
`https://gateway.aidp.eu-frankfurt-1.oci.oraclecloud.com/agentendpoint/6273a6c2-4e07-4e40-ab24-8a44c9475f69/chat`

The agent configuration now uses on-demand Custom Code calculations for scenarios and alternatives. Hosted-agent execution and application rendering were verified for an explicit 13,200-unit candidate, a Carrefour comparison and the Monoprix four-day simulation. No stored solution table is referenced by the flow. The FIN-01 retrieval test cited `/Volumes/gold/bic_gold/bic_policy_docs/FIN-01.txt#chunk_0`, version 1.2, with a 25% minimum margin. The UI renders a safe summary of tools actually called; it does not synthesize a reasoning trace.

## Boundaries for the presenter

- All source facts are demonstration data in Object Storage. The existing strategy PowerPoint in `Demo_BIC/` was preserved.
- The pipeline trained the models in AIDP. Their held-out metrics are measured on synthetic labels and do not establish BIC production performance.
- The app evaluates sliders locally with the exported weights and identical calculation code. The live agent calls Custom Code tools using the current slider values and optional user-specified transfer quantity. Source inputs, policies and model weights are a versioned cached snapshot from Object Storage; results are calculated during the question. This is not a per-keystroke Spark call or registered model-serving endpoint.
- Approval, manager escalation and decision JSON export are an application workflow rehearsal. Role buttons are not production identity enforcement.
- No JDE connection exists. Nothing is reserved, sent to a distributor or transmitted to JDE. JDE EnterpriseOne integration is an architecture discussion only, subject to the customer's installed version and implementation choices.
- The demo uses the Agent Flows capability provisioned in this workspace. The verified deployment API is the workspace-scoped `20240831` interface; availability and payload compatibility must be checked in another tenancy.
- Runtime credentials stay in the presenter's OCI profile. No credentials or decision histories are included in the deliverable.

## Restart

From the package directory, with an authenticated OCI profile:

```bash
export OCI_CLI="$HOME/.local/bin/oci"  # adjust if needed
python3 scripts/sync_cloud_exports.py
bash scripts/start_aidp.sh
```

Keep the compute services warm for the meeting. Run the pipeline before rehearsal, not during the 25-minute presentation. Agent answers can vary in wording; numerical facts and policy statuses must match the scenario.
