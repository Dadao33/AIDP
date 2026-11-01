# BIC Agent Flow

The BIC flow is deployed and tested. See `../docs/DEPLOYMENT_STATUS.md` for identifiers and evidence. Its model is `openai.gpt-5.5`, bound to the existing AI Compute; successful endpoint calls verified that binding in this workspace.

## Reproduction order

1. Create the external policy volume using `create-volume.verified.json`.
2. Create the Knowledge Base using `create-knowledge-base.verified.json` and attach the source using `add-policy-source.verified.json`.
3. Start the source-ingestion job using the Knowledge Base API `/knowledgeBases/{catalog.schema.kb_name}/jobs/{job_name}/runs`, not the generic Jobs endpoint. Confirm eight records added before using retrieval.
4. Upload `custom_tool_bic_live_calculations.zip` to `/Workspace/BICDemo/agent/`. Create the minimal flow with `create-flow.verified.json`, then update its graph with `update-flow.verified.json`. Bind the returned flow key and current environment IDs. `create-flow.template.json` is an authoring reference, not the recommended create sequence.
5. POST `deploy-flow.verified.json` to `/workspaces/{workspace}/actions/deployAgentFlow`. For an existing deployment, POST `redeploy-flow.verified.json` to `/workspaces/{workspace}/actions/redeployAgentFlow`; it omits `displayName` to avoid a duplicate-name conflict.
6. Test national exceptions, Carrefour facts, Monoprix FIN-01 retrieval and Monoprix after changing the total delay from 3 to 4 days.

The graph runs START → GUARDRAILS → AGENT. Four read-only Spark SQL tools access baseline Gold facts. Four Custom Code tools calculate scenarios and candidate alternatives on request; the RAG tool queries `gold.bic_gold.kb_bic_b2b_policies`. The verified RAG input schema uses a string `query`.

English instructions and tools are in `instructions.md` and `tools.json`. No HTTP write tool is exposed. User questions remain untrusted. The app supplies the account, region, current slider values and scenario hash; the server rejects a stale hash before revealing solution controls. Numerical policy checks and final human approvals stay outside language generation.

The UI displays only actual tool names, outcomes and durations from the response trace. It does not expose raw service traces or hidden reasoning. Existing RetailNova and SPORT flows are separate and were not modified.
