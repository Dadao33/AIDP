import unittest,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from shared.engine import evaluate,solutions
read=lambda p:json.loads((ROOT/p).read_text())
C=read('data/raw/accounts.json');O={o['case_id']:o for o in read('data/raw/supply.json')};P=read('data/raw/policies.json');M=read('data/gold/model.json')
class Business(unittest.TestCase):
 def eval(self,id,**kw):
  c=next(c for c in C if c['id']==id);return evaluate(c,O[id],P,M,**kw)
 def opts(self,id,**kw):
  c=next(c for c in C if c['id']==id);return solutions(c,O[id],P,M,**kw)
 def test_four_exceptions(self):self.assertEqual([c['id'] for c in C if self.eval(c['id'])['short_days']],['OPP-001','OPP-002','OPP-007','OPP-019'])
 def test_carrefour_firm_and_forecast_are_distinct(self):
  x=self.eval('OPP-001');self.assertEqual((x['firm_units'],x['available_by_due'],x['firm_shortfall'],x['peak_shortfall']),(97350,82250,15100,21275))
 def test_monoprix_temporary_gap(self):
  x=self.eval('OPP-007');self.assertEqual(x['firm_shortfall'],0);self.assertEqual(x['short_dates'],['2026-08-26','2026-08-27']);self.assertEqual(x['recovery_date'],'2026-08-28');self.assertEqual(x['peak_shortfall'],17155)
 def test_leclerc_moderate_score_still_requires_attention(self):
  x=self.eval('OPP-002');self.assertLess(x['risk'],.42);self.assertEqual(x['peak_shortfall'],5280)
 def test_monoprix_margin_block(self):
  t=self.opts('OPP-007')[0];self.assertEqual(t['quantity'],18000);self.assertEqual(t['status'],'BLOCKED');self.assertLess(t['margin_after_freight'],.25)
 def test_simulation_changes_solutions_and_snapshot(self):
  a=self.eval('OPP-007');b=self.eval('OPP-007',delay=4);self.assertNotEqual(a['context_hash'],b['context_hash']);self.assertEqual(b['peak_shortfall'],30190);self.assertEqual(self.opts('OPP-007',delay=4)[0]['quantity'],31200)
 def test_no_duplicate_receipt_on_acceleration(self):
  o=self.opts('OPP-001')[1];self.assertLessEqual(o['quantity'],O['OPP-001']['receipt_units']);self.assertEqual(o['status'],'BLOCKED')
 def test_invalid_scenario(self):
  for promo,delay in [(float('nan'),1),(.7,1),(.2,6),(.205,1)]:
   with self.assertRaises(ValueError):self.eval('OPP-001',promo=promo,delay=delay)
 def test_entire_scenario_grid(self):
  count=0
  for c in C:
   for uplift in range(61):
    for delay in range(5):
     x=evaluate(c,O[c['id']],P,M,uplift/100,delay);opts=solutions(c,O[c['id']],P,M,uplift/100,delay)
     self.assertEqual(sum(r['daily'] for r in x['points']),x['forecast_units']);self.assertEqual(x['firm_shortfall'],max(0,x['firm_units']-x['available_by_due']));self.assertEqual(x['available_by_due'],x['allocated_units']+x['future_receipts_by_due']);self.assertGreaterEqual(x['forecast_units'],x['firm_units'])
     if opts:
      t=opts[0];self.assertLessEqual(t['quantity'],x['mobilizable']);self.assertEqual(t['quantity']%c['pack_size'],0)
     count+=1
  self.assertEqual(count,7930)
if __name__=='__main__':unittest.main()
