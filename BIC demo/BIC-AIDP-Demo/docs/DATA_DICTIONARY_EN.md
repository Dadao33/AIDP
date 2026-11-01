# Data dictionary and business semantics

Snapshot: 24 August 2026. Forecast horizon: 25–31 August. All monetary values are EUR net of VAT. Product units are individual items; a selling box and a shipping multiple are separate quantities.

## Source files

| File | Grain and purpose |
|---|---|
| accounts.json | One regional distributor / product scenario, 26 rows; firm units, net price, gross-margin rate, pack size, promotion uplift and model inputs |
| supply.json | One case, 26 rows; allocation, dated receipts, incident evidence, donor stock and transport/acceleration terms |
| policies.json | One versioned policy bundle with eight rules, thresholds and case-specific protected donor stock |
| budget.json | One budget bundle, with 26 same-week account revenue budgets |
| historical_snapshots.csv | 96 historical series × 84 weekly snapshots = 8,064 observations; point-in-time predictors and future outcome labels |

History is independent synthetic training evidence. Labels are not actual BIC outcomes. The chronological split is 60 weeks train, 12 validation, 12 untouched test; there is no random train/test leakage across the same weeks.

## Published Gold tables

| Table under gold.bic_gold | Grain |
|---|---|
| account_context | 26 baseline accounts; exception quantities, risk and full dated context JSON |
| policies | Eight source rules, owner, version and effective dates |
| financial_outlook | 26 baseline revenue budgets, forecast revenue, gross margin and exposure |
| model_performance | Model version, MLflow run ID and measured evaluation metrics |

## Quantities

- Firm units: committed order quantity. Do not add the weekly forecast to it.
- Forecast units: model output bounded below by firm units. The curve distributes this weekly quantity using a planning profile.
- Allocated stock: already reserved for this case at the snapshot.
- Future receipts by due date: expected supply whose scenario arrival is no later than the promise date; not physically received stock.
- Firm shortfall: max(0, firm units − allocated stock − on-time future receipts).
- Daily cumulative gap: cumulative available supply − cumulative forecast demand. Negative values mean a date-specific coverage need.
- Peak shortfall: largest positive uncovered cumulative demand. Do not sum cumulative daily shortfalls.
- Risk score: estimated probability of at least one incomplete order line within seven days. It is neither the fraction of units missing nor proof of causality.
- Mobilizable donor stock: physical donor stock − other customer reservations − protected safety stock. Donor pools are independent case scenarios and cannot be summed as a national inventory.

## Money

Revenue budget and forecast revenue cover the same week and account scope. Forecast revenue = weekly forecast units × net unit price. Forecast gross margin = that revenue × gross-margin rate. Peak gross-margin exposure = peak uncovered units × price × margin rate. Exposure is neither a booked loss nor a guaranteed benefit from a remedy. Incremental freight is evaluated separately; do not subtract the same exposure twice.

## Scenario settings

Demand uplift is an integer from 0 to 60 percent. Total receipt delay is 0 to 4 days, measured from the original planned receipt. A slider change is a hypothesis; the original incident does not prove its cause. A changed scenario invalidates previously displayed solutions and their approval context.

## Policy status

PASS: the numerical condition is satisfied. BLOCKED: the option cannot be approved under the configured rule. REVIEW: explicit human review or external confirmation remains. A numerical PASS does not reserve stock or establish carrier capacity.
