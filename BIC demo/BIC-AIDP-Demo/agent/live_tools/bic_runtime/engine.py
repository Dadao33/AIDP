"""Shared deterministic tools used by notebooks, the cockpit and the agent.
No language model computes quantities, money, policy status or approvals.
"""
from datetime import date,timedelta
import math,hashlib,json
from .daily_forecast import daily_forecast

def fingerprint(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def score(c,model,promo,delay):
    v={**c,'promo_uplift':promo,'delay_days':delay}
    z=[(v[f]-m)/s*w for f,m,s,w in zip(model['features'],model['mean'],model['std'],model['weights'][1:])]
    risk=1/(1+math.exp(-max(-30,min(30,model['weights'][0]+sum(z)))))
    f=model['forecast_weights']
    learned=round(math.exp(f[0]+f[1]*math.log(c['daily_units_28d']*7)+f[2]*promo+f[3]*math.log(c['season_index'])))
    total=max(learned,c['order_units'])
    return {'risk':risk,'learned_forecast_units':learned,'forecast_units':total,'firm_floor_applied':total>learned,'daily':daily_forecast(c,total,promo),'drivers':[{'feature':k,'log_odds_contribution':round(x,4),'raw_value':v[k]} for k,x in zip(model['features'],z)]}

def evaluate(c,o,policy,model,promo=None,delay=None):
    promo=c['promo_uplift'] if promo is None else promo
    delay=c['delay_days'] if delay is None else delay
    if isinstance(promo,bool) or isinstance(delay,bool) or not isinstance(promo,(int,float)) or not isinstance(delay,(int,float)) or not math.isfinite(promo+delay) or not 0<=promo<=.6 or delay not in range(5) or abs(promo*100-round(promo*100))>1e-6:
        raise ValueError('Demand uplift must be a whole percentage from 0 to 60; delay must be 0 to 4 whole days.')
    s=score(c,model,promo,delay); snapshot=date.fromisoformat(o['snapshot'])
    dt=lambda n:(snapshot+timedelta(days=n)).isoformat()
    receipts={}
    for day,qty in [(o['early_receipt_days'],o['confirmed_early_receipt_units']),(o['planned_receipt_days']+delay,o['receipt_units'])]:receipts[dt(day)]=receipts.get(dt(day),0)+qty
    available=o['allocated_units'];cum=0;points=[{'date':o['snapshot'],'daily':0,'receipts':0,'demand':0,'supply':available,'gap':available}]
    for r in s['daily']:
        arrived=receipts.get(r['date'],0);available+=arrived;cum+=r['units'];points.append({'date':r['date'],'daily':r['units'],'receipts':arrived,'demand':cum,'supply':available,'gap':available-cum})
    gaps=[p for p in points if p['gap']<0];peak=max([0]+[-p['gap'] for p in gaps]);firm=max(0,c['order_units']-available)
    recovery=next((p['date'] for p in points if gaps and p['date']>gaps[-1]['date'] and p['gap']>=0),None)
    mobilizable=max(0,o['donor_physical_units']-o['donor_committed_units']-policy['donor_safety_units'][c['id']])
    plan={'case_id':c['id'],'promo_pct':round(promo*100),'delay_days':delay,'snapshot':o['snapshot'],'policy_version':policy['version'],'model_version':model['version']}
    # Spark promotes mixed numeric arrays to doubles. Normalize that field for stable cross-runtime hashes.
    hash_account={**c,'promotion_daily_weights':[float(w) for w in c['promotion_daily_weights']]}
    plan['context_hash']=fingerprint({**plan,'account':hash_account,'supply':o,'policy':policy,'model':model})
    return {**plan,'customer':c['customer'],'retailer':c['retailer'],'region':c['region_name'],'region_code':c['region_code'],'product':c['product'],'sku':c['sku'],'photo_key':c['photo_key'],'unit_price':c['unit_price'],'margin_rate':c['margin_rate'],'firm_units':c['order_units'],'allocated_units':o['allocated_units'],'future_receipts_by_due':available-o['allocated_units'],'available_by_due':available,'firm_shortfall':firm,'forecast_end_shortfall':max(0,-points[-1]['gap']),'peak_shortfall':peak,'short_days':len(gaps),'short_dates':[p['date'] for p in gaps],'recovery_date':recovery,'receipt_date':dt(o['planned_receipt_days']+delay),'original_receipt_date':dt(o['planned_receipt_days']),'receipt_units':o['receipt_units'],'event':o['event_reason'] if delay==o['event_delay_days'] else 'User scenario: total inbound delay changed. The original event does not establish the cause of this hypothesis.','event_reference':o['event_reference'],'promise_date':o['promise_date'],'points':points,'donor':'BIC Centre Warehouse','receiver':o['destination'],'donor_physical':o['donor_physical_units'],'donor_reserved':o['donor_committed_units'],'donor_safety':policy['donor_safety_units'][c['id']],'mobilizable':mobilizable,'pack_size':c['pack_size'],**{k:v for k,v in s.items() if k!='daily'}}

def solutions(c,o,p,m,promo=None,delay=None,transfer_quantity=None):
    x=evaluate(c,o,p,m,promo,delay);firm=x['firm_shortfall'];peak=x['peak_shortfall'];pack=c['pack_size']; snapshot=date.fromisoformat(o['snapshot'])
    # Firm remediation: floor packs so no excess order quantity is allocated.
    # Forecast prevention: ceil to a full pack, explicitly requiring commercial approval.
    q=(min(firm,x['mobilizable'])//pack*pack) if firm else min(math.ceil(peak/pack)*pack,x['mobilizable']//pack*pack)
    if transfer_quantity is not None:
        if isinstance(transfer_quantity,bool) or not isinstance(transfer_quantity,(int,float)) or not math.isfinite(transfer_quantity) or transfer_quantity<0 or transfer_quantity!=int(transfer_quantity):
            raise ValueError('Transfer quantity must be a non-negative whole number of units.')
        q=int(transfer_quantity)
    target=o['promise_date'] if firm else (x['short_dates'][0] if peak else o['promise_date'])
    arrival=(snapshot+timedelta(days=c['transfer_days'])).isoformat()
    expedite=(snapshot+timedelta(days=max(0,o['planned_receipt_days']+x['delay_days']-o['expedite_days_saved']))).isoformat()
    def check(id,ok,detail,status=None):return {'id':id,'status':status or ('PASS' if ok else 'BLOCKED'),'detail':detail}
    def after_timeline(qty,day):
        return [{**r,'supply':r['supply']+(qty if r['date']>=day else 0),'gap':r['gap']+(qty if r['date']>=day else 0)} for r in x['points']]
    margin=c['margin_rate']-c['freight']/(q*c['unit_price']) if q else None
    checks=[check('GOV-01',p['effective_from']<=o['snapshot']<=p['effective_to'],'Policy v'+p['version']),check('STK-01',q<=x['mobilizable'],f"{q:,} units studied / {x['mobilizable']:,} mobilizable"),check('LOG-01',q>0 and q%pack==0,f'Shipping multiple: {pack:,} units'),check('SLA-01',arrival<=target,f'Arrival {arrival}; required by {target}'),check('FIN-01',margin is not None and margin>=p['thresholds']['minimum_margin_rate'],f"Margin after freight: {margin:.3%}; minimum {p['thresholds']['minimum_margin_rate']:.3%}" if margin is not None else 'No positive transfer quantity'),check('AUT-01',False,'Human cost approval required',status='REVIEW')]
    if not firm and q:checks.append(check('CLI-01',False,'Additional forecast cover requires commercial confirmation; it is not a new customer promise',status='REVIEW'))
    if firm>q:checks.append(check('CLI-01',False,f'{firm-q:,} firm units remain uncovered; account manager review required',status='REVIEW'))
    if firm and q>firm:checks.append(check('CLI-01',False,f'{q-firm:,} units exceed the firm shortfall; commercial confirmation required',status='REVIEW'))
    roles=['Operations'] if c['freight']<=500 else (['Supply chain manager'] if c['freight']<=1500 else ['Supply chain director','Finance'])
    if not firm or firm!=q:roles.append('Account manager')
    after=after_timeline(q,arrival)
    transfer={'id':'transfer','title':'Internal BIC transfer','quantity':q,'arrival':arrival,'cost':c['freight'],'margin_after_freight':margin,'donor':x['donor'],'receiver':x['receiver'],'firm_remaining':max(0,firm-q) if arrival<=o['promise_date'] else firm,'peak_remaining':max([0]+[-r['gap'] for r in after]),'policy_checks':checks,'required_roles':roles,'purpose':'Firm order remediation' if firm else 'Forecast coverage prevention'}
    expq=min(o['receipt_units'],firm or peak); expmargin=c['margin_rate']-o['expedite_cost_estimate']/(max(1,expq)*c['unit_price'])
    acceleration={'id':'expedite','title':'Accelerate factory receipt','quantity':expq,'arrival':expedite,'cost':o['expedite_cost_estimate'],'margin_after_freight':expmargin,'donor':o['origin'],'receiver':x['receiver'],'firm_remaining':max(0,firm-expq) if expedite<=o['promise_date'] else firm,'policy_checks':[check('SUP-01',o['expedite_confirmed'],'Factory capacity and transport are not confirmed'),check('FIN-01',expmargin>=.25,f'Margin after freight {expmargin:.1%}; minimum 25%'),check('SLA-01',expedite<=target,f'Arrival {expedite}; required by {target}'),check('AUT-01',False,'Cost delegation approval required',status='REVIEW')],'required_roles':['Supply chain director','Finance'],'purpose':'Conditional acceleration; not an additional receipt'}
    split={'id':'split','title':'Negotiate split delivery','quantity':0,'arrival':o['promise_date'],'cost':None,'margin_after_freight':None,'firm_remaining':firm,'policy_checks':[check('CLI-01',o['split_customer_approved'],'No documented distributor agreement'),check('AUT-01',False,'Transport cost has not been quoted')],'required_roles':['Account manager','Supply chain manager'],'purpose':'Changes the promise; does not create inventory'}
    for opt in (transfer,acceleration,split):opt['status']='BLOCKED' if any(c['status']=='BLOCKED' for c in opt['policy_checks']) else 'REVIEW'
    return [transfer,acceleration,split] if peak or firm else []
