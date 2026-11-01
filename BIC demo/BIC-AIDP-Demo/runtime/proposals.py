"""Validate the agent's runtime calculation receipts; never load stored alternatives.

The platform trace confirms invocation, while an independent local recalculation
checks the quantities and rule results against the same versioned input snapshot.
It is not a cryptographic signature of the provider's trace (tool outputs are redacted).
"""
import uuid
from datetime import datetime, timezone
from shared.engine import solutions, fingerprint

TOOLS={'transfer':'evaluate_transfer','expedite':'evaluate_expedite','split':'evaluate_split'}

def validate_evaluations(result,x,c,o,p,m,mode):
    receipts=result.get('evaluations',[])
    if not isinstance(receipts,list) or len(receipts)>3:raise ValueError('Invalid calculation receipts')
    if not receipts:return []
    if not x or result.get('context_hash')!=x['context_hash']:raise ValueError('The agent used a different scenario snapshot. Recalculate for the current scenario.')
    called={t['tool'] for t in result.get('tool_activity',[]) if not t.get('failed')}
    opts=[];seen=set()
    for r in receipts:
        kind=r.get('option_id')
        if kind not in TOOLS or kind in seen:raise ValueError('Unknown or duplicate evaluated alternative')
        if mode=='aidp' and TOOLS[kind] not in called:raise ValueError('No successful AIDP calculation tool call for this alternative')
        if r.get('context_hash')!=x['context_hash']:raise ValueError('Calculation receipt has an obsolete scenario')
        uuid.UUID(r['evaluation_id'])
        stamp=datetime.fromisoformat(r['calculated_at'])
        if stamp.tzinfo is None or not -60 <= (datetime.now(timezone.utc)-stamp).total_seconds() <= 900:raise ValueError('Calculation receipt is stale')
        quantity=r.get('quantity_units')
        expected=next((v for v in solutions(c,o,p,m,x['promo_pct']/100,x['delay_days'],transfer_quantity=quantity if kind=='transfer' else None) if v['id']==kind),None)
        if expected is None or expected['quantity']!=quantity or fingerprint(expected)!=r.get('result_hash'):
            raise ValueError('Agent calculation does not match the source snapshot and policy checks. No alternative applied.')
        expected.update(evaluation_id=r['evaluation_id'],calculated_at=r['calculated_at'],calculation_mode='on_demand',result_hash=r['result_hash'])
        opts.append(expected);seen.add(kind)
    recommended=result.get('recommended_solution_id')
    if recommended and recommended not in seen:raise ValueError('Recommendation has no evaluated alternative')
    if recommended and next(v for v in opts if v['id']==recommended)['status']=='BLOCKED':
        raise ValueError('A blocked alternative cannot be recommended for approval')
    return opts
