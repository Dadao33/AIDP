-- Run with the supplied Spark compute. BIC tables only.
SELECT COUNT(*) AS accounts FROM gold.bic_gold.account_context; -- 26
SELECT COUNT(*) AS policies FROM gold.bic_gold.policies; -- 8
SELECT case_id, customer, risk, firm_shortfall, peak_shortfall, short_days
FROM gold.bic_gold.account_context WHERE short_days > 0 ORDER BY case_id;
-- OPP-001, OPP-002, OPP-007, OPP-019; do not filter by score alone.
SELECT * FROM gold.bic_gold.model_performance;
-- Runtime candidates: verify Custom Code traces, receipts and tests/test_live_receipts.py.
