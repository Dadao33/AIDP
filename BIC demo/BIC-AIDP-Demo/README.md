# BIC Retail Studio — AIDP demo package

A 25-minute B2B retail decision journey for a BIC France Customer Service & Supply Chain Manager. BIC is the supplier. The distributors are illustrative regional account scopes.

## Start here

1. Read `docs/DEPLOYMENT_STATUS.md` for the actual verified cloud state.
2. Present `presentation/BIC_AIDP_25min_EN.pptx` (six main slides, two hidden appendices).
3. Follow `docs/DEMO_GUIDE_FR.pdf` or `.html`: French presenter notes, English spoken dialogue and questions, exact timings and expected values.
4. Start the English cockpit with `python3 runtime/server.py --port 8766` from this directory. Python 3.9+ suffices for serving the packaged model. Default mode is explicitly labelled **rehearsal**.
5. For the real AIDP agent, use `scripts/start_aidp.sh` after configuring OCI CLI authentication and syncing the cloud exports. The agent never silently falls back to rehearsed answers.

## Contents

| Folder | Contents |
|---|---|
| `data/raw` | 26 accounts, dated supply events, budget, policies and 8,064 historical observations |
| `data/gold` | Published model, account facts and provenance manifest |
| `notebooks` | Four executable AIDP notebooks, also supplied as readable Python sources |
| `shared` | Identical forecasting, scoring, coverage and policy calculations for cloud and app |
| `agent` | English instructions, four Custom Code calculators, four SQL readers, policy retrieval and flow payloads |
| `policies` | Eight versioned, individually readable policy documents |
| `pipeline` | Verified job payloads and ordered task plan for AIDP Jobs |
| `runtime`, `web` | Local English cockpit and signed AIDP gateway client |
| `scripts`, `sql`, `tests` | Upload, cloud sync, launch, diagnostics and business invariants |
| `docs`, `presentation` | Setup, data dictionary, architecture, guide, evidence and PowerPoint |

## Data boundary

Source: `oci://AIDP_DATA@frn9volod3kr/Demo_BIC/bic-retail-v1/`.
The existing file `Demo_BIC/AI Strategy 4 LDC - Nov 2026.pptx` is not modified.
JDE appears only in the target architecture discussion. No JDE connection, reservation, order mutation or external message is implemented. Decision approval is a local workflow rehearsal, with JSON export only.

The demonstration data and model labels are synthetic. Product names and retailer brands identify the scenario, not a confirmed commercial relationship. Runtime traces are real when mode is AIDP; performance metrics do not establish BIC production accuracy.

## Reproducibility

`python3 -m unittest discover -s tests -v` checks business and decision invariants. To retrain locally, install NumPy in a separate environment and run `python3 scripts/build_local_gold.py`; this changes the provenance to local rehearsal. Before reconnecting to AIDP, run `python3 scripts/sync_cloud_exports.py` to restore the exact cloud model and verify scenario hashes.

No credentials, private OCI configuration, session tokens or decision histories are distributed in this package.
