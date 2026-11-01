from pathlib import Path
import json,shutil,hashlib,zipfile
P=Path(__file__).resolve().parents[1]
D=P/'agent/live_tools'
(D/'bic_runtime').mkdir(exist_ok=True);(D/'inputs').mkdir(exist_ok=True)
(D/'__init__.py').write_text('');(D/'bic_runtime/__init__.py').write_text('')
for name in ('engine.py','daily_forecast.py'):shutil.copy2(P/'shared'/name,D/'bic_runtime'/name)
files={'accounts.json':'data/raw/accounts.json','supply.json':'data/raw/supply.json','policies.json':'data/raw/policies.json','model.json':'data/gold/model.json'}
for name,rel in files.items():shutil.copy2(P/rel,D/'inputs'/name)
manifest={'snapshot_id':'bic-20260824-v1','source':'oci://AIDP_DATA@frn9volod3kr/Demo_BIC/bic-retail-v1/','loading':'Versioned Object Storage input snapshot, cached in the agent execution package. Not a live ERP read. No computed alternatives are included.','sha256':{n:hashlib.sha256((D/'inputs'/n).read_bytes()).hexdigest() for n in files}}
(D/'inputs/source_manifest.json').write_text(json.dumps(manifest,indent=2))
schema=[{'name':'case_id','type':'string','description':'Exact current account ID from trusted_context.'},{'name':'promo_pct','type':'number','description':'Current whole percentage uplift, 0 through 60. Copy trusted_context.'},{'name':'delay_days','type':'number','description':'Current total inbound delay, 0 through 4 days. Copy trusted_context.'}]
specs=[('BicScenarioCalculator','calculate_account_scenario','Compute forecast, risk, dated coverage, input evidence and inventory constraints now. No lookup of precomputed scenario rows.'),('BicTransferEvaluator','evaluate_transfer','Calculate a candidate warehouse transfer now: quantity, arrival, freight, margin, residual gaps and policy results. Supply quantity_units=-1 for the default policy sizing, or an explicit candidate quantity to test a user constraint. This is an evaluation, not a reservation.'),('BicAccelerationEvaluator','evaluate_expedite','Calculate bringing forward the existing factory receipt now, with estimated cost and policy checks. Never count it as additional supply.'),('BicSplitEvaluator','evaluate_split','Evaluate a negotiated split delivery now: no stock creation, residual firm deficit, missing customer consent and quotation. Not an approved promise change.')]
tools=[]
for cls,name,desc in specs:
    params=schema+([{'name':'quantity_units','type':'number','description':'Candidate transfer units. -1 uses policy sizing; an explicit nonnegative integer evaluates that candidate. Never silently change the user quantity.'}] if name=='evaluate_transfer' else [])
    tools.append({'toolClassName':cls,'displayName':name,'description':desc,'version':'2.0.0','schema':params,'conf':{}})
(D/'tool_config.json').write_text(json.dumps({'displayName':'BIC live decision calculations','description':'Calculates candidates only when requested by the agent','tools':tools},indent=2))
target=P/'agent/custom_tool_bic_live_calculations.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(D.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts:z.write(f,f.relative_to(D))
print(target, target.stat().st_size)
