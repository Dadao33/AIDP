"""Download AIDP Gold exports from the configured Object Storage prefix.
No credentials are stored. Verifies all baseline scenario hashes before installing files.
"""
from pathlib import Path
import sys,json,os,tempfile,subprocess,hashlib,argparse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from shared.engine import evaluate
p=argparse.ArgumentParser();p.add_argument('--oci',default=os.environ.get('OCI_CLI','oci'));a=p.parse_args()
config=json.loads((ROOT/'config/demo.json').read_text());uri=config['object_storage']['gold_export_uri'];bucket,rest=uri[6:].split('@',1);namespace,prefix=rest.split('/',1)
base=[a.oci,'os','object'];common=['--namespace-name',namespace,'--bucket-name',bucket,'--region',os.environ.get('AIDP_REGION','eu-frankfurt-1'),'--profile',os.environ.get('OCI_CONFIG_PROFILE','DEFAULT')];env={**os.environ,'OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING':'True'}
def run(args):
 r=subprocess.run(args,capture_output=True,text=True,env=env,timeout=120)
 if r.returncode:raise RuntimeError(r.stderr[-600:])
 return r.stdout
with tempfile.TemporaryDirectory(prefix='bic-gold-') as temp:
 rows={}
 for part in ['accounts','model']:
  listing=json.loads(run(base+['list',*common,'--prefix',prefix+'/'+part+'/','--all']))['data'];names=[i['name'] for i in listing if i['name'].endswith('.json')]
  if not names:raise RuntimeError('No Gold export for '+part)
  rows[part]=[]
  for i,name in enumerate(names):
   f=Path(temp)/(part+str(i)+'.json');run(base+['get',*common,'--name',name,'--file',str(f)]);rows[part]+=[json.loads(l) for l in f.read_text().splitlines() if l]
 model=json.loads(rows['model'][0]['model_json']);accounts=[json.loads(r['context_json']) for r in rows['accounts']]
 raw=ROOT/'data/raw';cases=json.loads((raw/'accounts.json').read_text());supply={o['case_id']:o for o in json.loads((raw/'supply.json').read_text())};policy=json.loads((raw/'policies.json').read_text())
 indexed={x['case_id']:x for x in accounts};mismatches=[]
 for c in cases:
  x=evaluate(c,supply[c['id']],policy,model)
  if x['context_hash']!=indexed[c['id']]['context_hash']:mismatches.append(c['id'])
 if mismatches:raise RuntimeError('Cloud/local scenario hashes differ; do not activate live mode: '+','.join(mismatches))
 out=ROOT/'data/gold';(out/'model.json').write_text(json.dumps(model,indent=2));(out/'accounts.json').write_text(json.dumps(accounts,indent=2,ensure_ascii=False));(out/'manifest.json').write_text(json.dumps({'mode':'aidp_object_storage_export','batch_id':config['batch_id'],'snapshot':config['demo']['as_of'],'accounts':len(accounts),'mlflow_run_id':model.get('mlflow_run_id'),'raw_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(raw.glob('*'))},'data_kind':'synthetic'},indent=2));print('Installed verified cloud exports:',len(accounts),'accounts; MLflow',model.get('mlflow_run_id'))
