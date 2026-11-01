# Verification evidence

Verified on 30 October 2026 in the user's BIC AIDP workspace.

## Cloud execution

- Object Storage source reads succeeded from Spark.
- All four pipeline tasks completed in sequence; the job reported SUCCESS.
- Bronze ingestion, Silver quality checks, MLflow training and Gold publication ran in AIDP.
- Gold contains 26 baseline account contexts. Scenario and alternative outputs are calculated on demand; notebook 04 no longer publishes a scenario grid or solution table.
- The Knowledge Base ingestion reported eight documents added. A live RAG answer retrieved FIN-01 version 1.2 and cited its chunk.
- The signed hosted-agent endpoint answered national, account, policy and simulated-scenario questions. No rehearsal answer was substituted.
- The latest cloud exports passed all 26 baseline hash comparisons before installation in the local app.

Resource IDs and the current model run are recorded in DEPLOYMENT_STATUS.md. Raw service responses are deliberately not distributed because they contain internal service metadata.

## Business invariants — 21 tests passed on 31 October

Nine calculation tests cover Carrefour's firm/forecast distinction, the four dated exceptions, all 7,930 supported scenarios, invalid inputs, Leclerc's moderate-score exception, Monoprix's temporary gap and margin block, receipt acceleration without duplicate stock, and changed simulation hashes/solutions.

Five local HTTP tests cover approval prerequisites, manager escalation for blocked options, rejection of stale scenario decisions and rejection of a foreign browser origin. Tests use a temporary decision store.

Key outcomes:

| Case | Due-date firm deficit | Peak forecast gap | Decision issue |
|---|---:|---:|---|
| Carrefour, 35% uplift / 4 days | 15,100 | 21,275 | 14,400-unit transfer; 700 firm units still unresolved |
| E.Leclerc Île-de-France, 40% / 2 days | 0 | 5,280 | Temporary gap on 27 Aug despite moderate probability |
| Monoprix Île-de-France, 10% / 3 days | 0 | 17,155 | 18,000-unit transfer blocked at 20.9% margin |
| Monoprix Île-de-France, 10% / 4 days | 0 | 30,190 | 31,200-unit option; 25.6% margin; human reviews required |
| METRO Nouvelle-Aquitaine, baseline | 0 | 26,752 | Temporary gap; transfer fails margin policy |

The METRO slider defaults should always be read from the supplied account record; the guide uses Carrefour and Monoprix for the main presentation.

## User interface

National region filtering changes the KPI/chart scope without selecting an account. Account photographs, dated causes, cumulative coverage and adjacent simulation controls were checked. Options remain hidden until a remedy question. Changing the scenario clears previous solution controls. Clicking a solution reveals its donor/receiver and clickable PASS/BLOCKED/REVIEW policy checks. Actual AIDP tool activity is visible above the answer. Curves stay above the agent response.

## Presentation and guide

The eight-slide PowerPoint passed artifact integrity/layout checks and visual review. Six slides are in the 25-minute route; two are hidden appendices. The French guide has English dialogue, exact prompts, expected values, timing, setup and fallback wording. Its PDF was rendered and reviewed page by page.

These checks verify the demonstration, not production SLA, commercial benefit, BIC model accuracy or enterprise authorization.

## On-demand calculation revision verified on 31 October

- Four native Custom Code tools replaced the SQL scenario and alternative lookups in the deployed BIC flow. Existing policy retrieval and portfolio readers remain.
- A freely requested 13,200-unit Carrefour transfer was evaluated by the hosted agent: margin 24.986%, FIN-01 BLOCKED, firm remainder 1,900 units. The application rendered this exact alternative with a fresh calculation timestamp.
- A live Carrefour comparison returned all three evaluated alternatives, with 14,400 transfer units. The agent recommended the transfer for human review.
- A live Monoprix comparison at 10% uplift / 4 days returned 31,200 transfer units. All three numerical receipts matched an independent recalculation, and the trace included each corresponding evaluator.
- Twenty-one local tests passed, including the 7,930 scenario calculation invariants, explicit candidate sizing, tampered receipts, missing tool calls, blocked recommendations, approval prerequisites, escalation and stale scenarios.
- A live application HTTP test rejected preparation without an agent proposal and rejected a proposal after a simulation change. No decision was sent to JDE.

The native platform trace exposes successful tool invocations and timings but redacts tool I/O. Numerical receipt validation is an independent consistency check; it is not a cryptographically signed provenance chain. Legacy Gold scenario/alternative tables are retained unused, and the updated notebook no longer generates them.
