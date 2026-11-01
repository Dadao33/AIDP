"""Loopback cockpit. Cloud agent optional; decision workflow is an explicit rehearsal.
JDE is narrative only. This process has no JDE network/write implementation.
"""
from pathlib import Path
import sys,json,os,uuid,threading,argparse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,unquote
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from shared.engine import evaluate,solutions,fingerprint
from runtime.aidp_client import chat
from runtime.proposals import validate_evaluations
read=lambda p:json.loads((ROOT/p).read_text())
CASES=read('data/raw/accounts.json');SUPPLY={o['case_id']:o for o in read('data/raw/supply.json')};POLICY=read('data/raw/policies.json');MODEL=read('data/gold/model.json');MODE=os.environ.get('BIC_MODE','rehearsal')
if MODE not in ('rehearsal','aidp'):raise RuntimeError('BIC_MODE must be rehearsal or aidp')
STORE=ROOT/'.runtime/decisions.json';LOCK=threading.RLock();DECISIONS=json.loads(STORE.read_text()) if STORE.exists() else []
PROPOSALS={}
def save():
    STORE.parent.mkdir(exist_ok=True);tmp=STORE.with_suffix('.tmp');tmp.write_text(json.dumps(DECISIONS,indent=2));tmp.replace(STORE)
def case(id):
    c=next((c for c in CASES if c['id']==id),None)
    if not c:raise ValueError('Unknown account')
    return c

def context(b):
    c=case(b.get('case_id'));return evaluate(c,SUPPLY[c['id']],POLICY,MODEL,b.get('promo_pct',round(c['promo_uplift']*100))/100,b.get('delay_days',c['delay_days']))
def options(x):
    c=case(x['case_id']);return solutions(c,SUPPLY[c['id']],POLICY,MODEL,x['promo_pct']/100,x['delay_days'])
def summary(x):
    return (f"{x['customer']}: {x['firm_shortfall']:,} firm units uncovered by {x['promise_date']}; peak forecast coverage gap {x['peak_shortfall']:,} units across {x['short_days']} day(s). " + (f"Recovery expected {x['recovery_date']}. " if x['recovery_date'] else '') + x['event'])
def rehearsal(q,x,region):
    low=q.lower();offer=any(w in low for w in ('solution','resolve','remed','prevent','transfer','compare','action','protect','fix'))
    if x:
        opts=options(x);answer=summary(x)
        if any(w in low for w in ('score','probability','risk')):answer+=f"\n\nThe {x['risk']:.1%} score estimates the probability of at least one incomplete order line in seven days. It is not the percentage of units missing. The dated supply event explains the operational gap; model contributions are associations."
        if offer and opts:
            t=opts[0];answer+=f"\n\nInternal transfer: {t['quantity']:,} units, arrival {t['arrival']}, freight EUR {t['cost']:,}. " + ('FIN-01 or another policy blocks the option. Escalate for review; do not execute.' if t['status']=='BLOCKED' else 'Review the residual need and obtain the required human approvals before committing.')
        elif offer:answer+='\n\nNo current coverage gap. Confirm inbound receipts and monitor; a high score alone does not justify spending.'
        receipts=[{'option_id':o['id'],'quantity_units':o['quantity'],'evaluation_id':str(uuid.uuid4()),'calculated_at':datetime.now(timezone.utc).isoformat(),'context_hash':x['context_hash'],'result_hash':fingerprint(o)} for o in opts] if offer else []
        return {'answer':answer,'evaluations':receipts,'policy_ids':['STK-01','FIN-01','AUT-01'] if offer else [],'account_ids':[x['case_id']],'context_hash':x['context_hash'],'recommended_solution_id':None}
    xs=[evaluate(c,SUPPLY[c['id']],POLICY,MODEL) for c in CASES];xs=[x for x in xs if not region or x['region_code']==region];affected=sorted((x for x in xs if x['short_days'] or x['firm_shortfall']),key=lambda x:(-x['firm_shortfall'],-x['peak_shortfall']))
    answer=f"{len(affected)} of {len(xs)} regional accounts have a dated coverage gap. This queue includes operational exceptions even when their probability score is moderate.\n\n"+'\n\n'.join(summary(x) for x in affected)
    return {'answer':answer,'solution_ids':[],'policy_ids':[],'account_ids':[x['case_id'] for x in affected]}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'web'),**kw)
    def safe(self):
        hosts={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        return self.headers.get('Host') in hosts and (not self.headers.get('Origin') or self.headers['Origin'] in {'http://'+h for h in hosts})
    def reply(self,status,obj):
        data=json.dumps(obj,ensure_ascii=False,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.safe():return self.reply(403,{'error':'Local origin required'})
        path=urlparse(self.path).path
        if path=='/api/bootstrap':return self.reply(200,{'accounts':[evaluate(c,SUPPLY[c['id']],POLICY,MODEL) for c in CASES],'policies':POLICY,'model':MODEL,'mode':MODE,'decisions':DECISIONS,'data_origin':read('data/gold/manifest.json').get('mode'),'budget':read('data/raw/budget.json')})
        if path=='/api/health':return self.reply(200,{'ok':True,'agent_mode':MODE,'agent_configured':bool(os.environ.get('AIDP_AGENT_CHAT_URL')),'calculation_mode':'on_demand','jde_connected':False,'workflow_mode':'rehearsal'})
        candidate=(ROOT/'web'/unquote(path).lstrip('/')).resolve()
        if path=='/':self.path='/index.html'
        elif (ROOT/'web').resolve() not in candidate.parents or candidate.is_dir():return self.reply(404,{'error':'Not found'})
        return super().do_GET()
    def do_POST(self):
        if not self.safe():return self.reply(403,{'error':'Local origin required'})
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<16000:raise ValueError('Invalid request size')
            b=json.loads(self.rfile.read(size));path=urlparse(self.path).path
            if path=='/api/scenario':return self.reply(200,context(b))
            if path=='/api/chat':
                q=b.get('question','').strip()
                if not 2<=len(q)<=2000:raise ValueError('Enter a question of 2 to 2000 characters')
                x=context(b) if b.get('case_id') else None
                ctx={'case_id':x['case_id'],'promo_pct':x['promo_pct'],'delay_days':x['delay_days'],'context_hash':x['context_hash']} if x else {'scope':'portfolio','region_code':b.get('region_code')}
                result=chat(q,ctx,'bic-'+uuid.uuid4().hex) if MODE=='aidp' else rehearsal(q,x,b.get('region_code'))
                result['solutions']=validate_evaluations(result,x,case(x['case_id']) if x else None,SUPPLY[x['case_id']] if x else None,POLICY,MODEL,MODE)
                if result['solutions']:
                    proposal_id='BIC-PROP-'+uuid.uuid4().hex
                    with LOCK:PROPOSALS[proposal_id]={'context_hash':x['context_hash'],'case_id':x['case_id'],'solutions':result['solutions'],'receipts':result['evaluations'],'mode':MODE}
                    result['proposal_id']=proposal_id
                result['policy_ids']=[id for id in result.get('policy_ids',[]) if id in {p['id'] for p in POLICY['rules']}]
                result['account_ids']=[id for id in result.get('account_ids',[]) if id in {c['id'] for c in CASES}];result['mode']=MODE
                return self.reply(200,result)
            if path=='/api/decision':
                x=context(b)
                proposal=PROPOSALS.get(b.get('proposal_id'))
                if not proposal or proposal['context_hash']!=x['context_hash'] or proposal['case_id']!=x['case_id']:raise ValueError('Ask the agent to calculate fresh solutions for this scenario before preparing a decision.')
                opt=next((v for v in proposal['solutions'] if v['id']==b.get('option_id')),None)
                if not opt:raise ValueError('Choose an alternative evaluated by the agent')
                if b.get('context_hash')!=x['context_hash']:raise ValueError('Scenario changed. Request fresh solutions first.')
                action=b.get('action');record=None
                with LOCK:
                    if action in ('prepare','escalate'):
                        if action=='prepare' and opt['status']=='BLOCKED':raise ValueError('Blocked option: transfer the case to a manager')
                        record=next((d for d in DECISIONS if d.get('proposal_id')==b['proposal_id'] and d['option']['id']==opt['id']),None)
                        if not record:
                            record={'id':'BIC-DEC-'+uuid.uuid4().hex[:8].upper(),'proposal_id':b['proposal_id'],'calculation_receipt':next(r for r in proposal['receipts'] if r['option_id']==opt['id']),'context_hash':x['context_hash'],'case_id':x['case_id'],'customer':x['customer'],'scenario':{'promo_pct':x['promo_pct'],'delay_days':x['delay_days']},'option':opt,'status':'ESCALATED' if action=='escalate' else 'AWAITING_APPROVAL','approvals':[],'audit':[],'jde_connected':False,'workflow_mode':'rehearsal'};DECISIONS.append(record)
                        if action=='escalate':record['status']='ESCALATED';record['manager']='Supply chain manager';record['consulted']=['Finance'] if any(p['id']=='FIN-01' and p['status']=='BLOCKED' for p in opt['policy_checks']) else []
                    else:
                        record=next((d for d in DECISIONS if d['id']==b.get('decision_id')),None)
                        if not record or record.get('proposal_id')!=b['proposal_id'] or record['context_hash']!=x['context_hash'] or record['option']['id']!=opt['id']:raise ValueError('Decision snapshot mismatch')
                        if opt['status']=='BLOCKED' or record['status']=='ESCALATED':raise ValueError('Policy block or escalation prevents approval/export')
                        if action=='approve':
                            if record['status']=='EXPORT_READY':raise ValueError('Decision is already exported')
                            role=b.get('role')
                            if role not in opt['required_roles'] or b.get('reviewed') is not True:raise ValueError('Select a required reviewer and confirm review')
                            if role not in record['approvals']:record['approvals'].append(role)
                            record['status']='APPROVED' if set(record['approvals'])==set(opt['required_roles']) else 'PARTIALLY_APPROVED'
                        elif action=='export':
                            if record['status'] not in ('APPROVED','EXPORT_READY'):raise ValueError('All approvals required')
                            record['status']='EXPORT_READY';record['payload']={'request_id':record['id'],'case_id':x['case_id'],'sku':x['sku'],'quantity':opt['quantity'],'donor':opt.get('donor'),'receiver':opt.get('receiver'),'target_date':opt['arrival'],'freight_eur':opt['cost'],'scenario_hash':x['context_hash'],'policy_version':POLICY['version'],'approval_roles':record['approvals'],'purpose':'Illustrative target JDE integration contract; not sent'}
                        else:raise ValueError('Unknown action')
                    record['audit'].append({'at':datetime.now(timezone.utc).isoformat(),'action':action,'actor':b.get('role','Demo operator'),'mode':'rehearsal'});save()
                return self.reply(200,record)
            return self.reply(404,{'error':'Unknown endpoint'})
        except (ValueError,KeyError,TypeError) as e:return self.reply(400,{'error':str(e)})
        except Exception as e:return self.reply(502,{'error':str(e)})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);args=parser.parse_args();print(f'BIC Retail Studio / {MODE} / http://127.0.0.1:{args.port}',flush=True);ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
