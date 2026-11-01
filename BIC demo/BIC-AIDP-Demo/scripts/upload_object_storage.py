"""Upload BIC source facts to the configured prefix. Default: plan only."""
import argparse,subprocess,json,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--oci',default=os.environ.get('OCI_CLI','oci'));a=p.parse_args()
config=json.loads((ROOT/'config/demo.json').read_text());uri=config['object_storage']['raw_uri'];bucket,rest=uri[6:].split('@',1);namespace,prefix=rest.split('/',1)
plan=[{'file':str(f),'object':prefix+'/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted((ROOT/'data/raw').glob('*'))]
plan += [{'file':str(f),'object':prefix.rsplit('/',1)[0]+'/policies/'+f.stem+'.txt','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted((ROOT/'policies').glob('*.md'))]
folder=ROOT/'.aidp/payloads';folder.mkdir(parents=True,exist_ok=True);(folder/'object-storage-upload-plan.json').write_text(json.dumps({'bucket':bucket,'namespace':namespace,'objects':plan},indent=2));print(json.dumps({'bucket':bucket,'namespace':namespace,'prefix':prefix,'files':len(plan),'bytes':sum(p['bytes'] for p in plan),'apply':a.apply},indent=2))
if a.apply:
 for item in plan:
  cmd=[a.oci,'os','object','put','--namespace-name',namespace,'--bucket-name',bucket,'--name',item['object'],'--file',item['file'],'--no-overwrite','--region',os.environ.get('AIDP_REGION','eu-frankfurt-1'),'--profile',os.environ.get('OCI_CONFIG_PROFILE','DEFAULT')]
  r=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,'OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING':'True'},timeout=90)
  if r.returncode:raise SystemExit('Upload stopped: '+item['object']+'\n'+(r.stderr+r.stdout)[-600:])
  print('Uploaded',Path(item['file']).name)
 (ROOT/'.aidp/object-upload-receipt.json').write_text(json.dumps({'status':'uploaded','objects':plan},indent=2))
