"""AIDP invokes these tools at question time; no scenario or option results are stored.

The package contains a versioned input snapshot copied from the Object Storage
sources and the trained model export. It contains no decisions or alternatives.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, uuid, hashlib
from aidputils.agents.tools.custom_tools.base import CustomToolBase
from .bic_runtime.engine import evaluate, solutions, fingerprint

ROOT = Path(__file__).resolve().parent

def load_inputs(params):
    manifest=json.loads((ROOT/'inputs/source_manifest.json').read_text())
    loaded={}
    for name,expected in manifest['sha256'].items():
        raw=(ROOT/'inputs'/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError('Input snapshot integrity check failed')
        loaded[name]=json.loads(raw)
    cid=params.get('case_id')
    c=next((v for v in loaded['accounts.json'] if v['id']==cid),None)
    if c is None:raise ValueError('Unknown account ID')
    o=next(v for v in loaded['supply.json'] if v['case_id']==cid)
    promo=float(params.get('promo_pct',round(c['promo_uplift']*100)))
    delay=float(params.get('delay_days',c['delay_days']))
    if delay.is_integer():delay=int(delay)
    return c,o,loaded['policies.json'],loaded['model.json'],promo/100,delay,manifest

def stamp(x,manifest,tool_name,params):
    return {'schema_version':'bic.live-calculation.v1','execution_id':str(uuid.uuid4()),
            'calculated_at':datetime.now(timezone.utc).isoformat(),'execution_mode':'on_demand',
            'tool':tool_name,'case_id':x['case_id'],'context_hash':x['context_hash'],
            'scenario':{'promo_pct':x['promo_pct'],'delay_days':x['delay_days']},
            'source_snapshot':manifest['snapshot_id'],'input_parameters':params}

def scenario(params):
    c,o,p,m,promo,delay,manifest=load_inputs(params)
    x=evaluate(c,o,p,m,promo,delay)
    return {**stamp(x,manifest,'calculate_account_scenario',params),'scenario_result':x}

def option(params,kind):
    c,o,p,m,promo,delay,manifest=load_inputs(params)
    quantity=params.get('quantity_units')
    if quantity in (None,'',-1,'-1'):quantity=None
    else:quantity=float(quantity)
    x=evaluate(c,o,p,m,promo,delay)
    opts=solutions(c,o,p,m,promo,delay,transfer_quantity=quantity if kind=='transfer' else None)
    result=next((v for v in opts if v['id']==kind),None)
    output=stamp(x,manifest,'evaluate_'+kind,params)
    if result is None:
        return {**output,'option':None,'explanation':'No dated coverage gap in this scenario; no remedial spend justified.'}
    output['receipt']={'option_id':kind,'quantity_units':result['quantity'],
                       'evaluation_id':output['execution_id'],'calculated_at':output['calculated_at'],
                       'context_hash':x['context_hash'],'result_hash':fingerprint(result)}
    result['evaluation_id']=output['execution_id']
    result['calculated_at']=output['calculated_at']
    result['calculation_mode']='on_demand'
    result['context_hash']=x['context_hash']
    result['inputs_hash']=fingerprint({'scenario':x['context_hash'],'parameters':params,'tool':output['tool']})
    return {**output,'option':result}

@CustomToolBase.register
class BicScenarioCalculator(CustomToolBase):
    @classmethod
    def _execute_tool(cls,conf,runtime_params,**context_vars):
        return scenario(runtime_params)

@CustomToolBase.register
class BicTransferEvaluator(CustomToolBase):
    @classmethod
    def _execute_tool(cls,conf,runtime_params,**context_vars):
        return option(runtime_params,'transfer')

@CustomToolBase.register
class BicAccelerationEvaluator(CustomToolBase):
    @classmethod
    def _execute_tool(cls,conf,runtime_params,**context_vars):
        return option(runtime_params,'expedite')

@CustomToolBase.register
class BicSplitEvaluator(CustomToolBase):
    @classmethod
    def _execute_tool(cls,conf,runtime_params,**context_vars):
        return option(runtime_params,'split')
