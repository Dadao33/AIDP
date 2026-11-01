import unittest,uuid,json,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime import server
from runtime.proposals import validate_evaluations
from shared.engine import solutions,fingerprint
class ReceiptTests(unittest.TestCase):
 def setUp(self):
  self.x=server.context({'case_id':'OPP-001','promo_pct':35,'delay_days':4});self.c=server.case('OPP-001');self.o=server.SUPPLY['OPP-001']
 def result(self,q):
  opt=solutions(self.c,self.o,server.POLICY,server.MODEL,.35,4,transfer_quantity=q)[0]
  return {'context_hash':self.x['context_hash'],'evaluations':[{'option_id':'transfer','quantity_units':q,'context_hash':self.x['context_hash'],'evaluation_id':str(uuid.uuid4()),'calculated_at':datetime.now(timezone.utc).isoformat(),'result_hash':fingerprint(opt)}],'tool_activity':[{'tool':'evaluate_transfer','failed':False}]}
 def validate(self,r):return validate_evaluations(r,self.x,self.c,self.o,server.POLICY,server.MODEL,'aidp')
 def test_specific_candidate_computed(self):
  out=self.validate(self.result(13200));self.assertEqual(out[0]['quantity'],13200);self.assertEqual(out[0]['status'],'BLOCKED');self.assertAlmostEqual(out[0]['margin_after_freight'],.2498631476050831)
  self.assertIn('24.986%',next(p['detail'] for p in out[0]['policy_checks'] if p['id']=='FIN-01'))
 def test_tampered_receipt_rejected(self):
  r=self.result(13200);r['evaluations'][0]['quantity_units']=14400
  with self.assertRaises(ValueError):self.validate(r)
 def test_tool_call_required(self):
  r=self.result(14400);r['tool_activity']=[]
  with self.assertRaises(ValueError):self.validate(r)
 def test_no_default_tiles_from_old_ids(self):self.assertEqual(self.validate({'solution_ids':['transfer']}),[])
 def test_blocked_recommendation_rejected(self):
  r=self.result(13200);r['recommended_solution_id']='transfer'
  with self.assertRaises(ValueError):self.validate(r)
 def test_only_requested_option_displayed(self):self.assertEqual(len(self.validate(self.result(14400))),1)
 def test_fresh_scenario_required(self):
  r=self.result(14400);r['context_hash']='old'
  with self.assertRaises(ValueError):self.validate(r)
if __name__=='__main__':unittest.main()
