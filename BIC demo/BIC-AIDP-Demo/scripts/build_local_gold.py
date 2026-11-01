"""Rehearsal build from the same raw inputs and shared tools as AIDP."""
from pathlib import Path
import sys,json,csv,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from shared.engine import evaluate,solutions,fingerprint
from shared.ml import train
raw=ROOT/'data/raw';out=ROOT/'data/gold';out.mkdir(exist_ok=True)
cases=json.loads((raw/'accounts.json').read_text());supply={o['case_id']:o for o in json.loads((raw/'supply.json').read_text())};policy=json.loads((raw/'policies.json').read_text())
rows=list(csv.DictReader((raw/'historical_snapshots.csv').open()));model=train(rows);model['training_sha256']=hashlib.sha256((raw/'historical_snapshots.csv').read_bytes()).hexdigest()
(out/'model.json').write_text(json.dumps(model,indent=2));current=[evaluate(c,supply[c['id']],policy,model) for c in cases]
(out/'accounts.json').write_text(json.dumps(current,ensure_ascii=False,indent=2));manifest={'batch_id':'bic-20260824-v1','snapshot':'2026-08-24','mode':'local_rehearsal','accounts':len(cases),'historical_rows':len(rows),'raw_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw.glob('*'))},'data_kind':'synthetic'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'accounts':len(cases),'uncovered_accounts':sum(c['short_days']>0 for c in current),'metrics':model['metrics'],'forecast_wape':model['forecast_wape'],'baseline_wape':model['baseline_wape']},indent=2))
for x in current:
 if x['short_days']:print(x['case_id'],x['firm_shortfall'],x['peak_shortfall'],x['short_dates'],round(x['risk']*100,1))
