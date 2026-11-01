"""Decision gates tested via HTTP with a temporary store."""
import unittest,tempfile,threading,json,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime import server
class WorkflowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();server.STORE=Path(cls.tmp.name)/'decisions.json';server.DECISIONS=[]
  cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.port=cls.http.server_port;threading.Thread(target=cls.http.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
 def post(self,path,body,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  req=Request(f'http://127.0.0.1:{self.port}/api/'+path,data=json.dumps(body).encode(),headers=headers)
  try:
   with urlopen(req) as r:return r.status,json.load(r)
  except HTTPError as e:return e.code,json.load(e)
 def ctx(self,id,delay=None):
  b={'case_id':id}
  if delay is not None:b['delay_days']=delay
  status,x=self.post('scenario',b);self.assertEqual(status,200);return x
 def proposal(self,b):
  status,r=self.post('chat',{**b,'question':'Compare solutions for this scenario'});self.assertEqual(status,200,r);return r.get('proposal_id')
 def test_without_agent_evaluation_cannot_prepare(self):
  x=self.ctx('OPP-001');self.assertEqual(self.post('decision',{**x,'option_id':'transfer','action':'prepare'})[0],400)
 def test_export_requires_every_approval(self):
  x=self.ctx('OPP-001');b={k:x[k] for k in ['case_id','promo_pct','delay_days','context_hash']};b['option_id']='transfer';b['proposal_id']=self.proposal(b)
  status,d=self.post('decision',{**b,'action':'prepare'});self.assertEqual(status,200);b['decision_id']=d['id'];self.assertEqual(self.post('decision',{**b,'action':'export'})[0],400)
  roles=d['option']['required_roles'];self.assertEqual(len(roles),2)
  for i,role in enumerate(roles):
   status,d=self.post('decision',{**b,'action':'approve','role':role,'reviewed':True});self.assertEqual(status,200)
   if i==0:self.assertEqual(self.post('decision',{**b,'action':'export'})[0],400)
  status,d=self.post('decision',{**b,'action':'export'});self.assertEqual(status,200);self.assertFalse(d['jde_connected']);self.assertEqual(d['payload']['quantity'],14400);self.assertEqual(d['status'],'EXPORT_READY')
 def test_blocked_option_can_only_escalate(self):
  x=self.ctx('OPP-007');b={k:x[k] for k in ['case_id','promo_pct','delay_days','context_hash']};b['option_id']='transfer';b['proposal_id']=self.proposal(b);self.assertEqual(self.post('decision',{**b,'action':'prepare'})[0],400)
  status,d=self.post('decision',{**b,'action':'escalate'});self.assertEqual(status,200);self.assertIn('Finance',d['consulted']);self.assertEqual(self.post('decision',{**b,'action':'approve','decision_id':d['id'],'role':'Supply chain manager','reviewed':True})[0],400)
 def test_changed_simulation_rejects_old_snapshot(self):
  x=self.ctx('OPP-007');b={k:x[k] for k in ['case_id','promo_pct','delay_days','context_hash']};b.update(option_id='transfer',action='prepare',delay_days=4);self.assertEqual(self.post('decision',b)[0],400)
  fresh=self.ctx('OPP-007',4);self.assertNotEqual(fresh['context_hash'],x['context_hash']);b['context_hash']=fresh['context_hash'];b['proposal_id']=self.proposal(b);status,d=self.post('decision',b);self.assertEqual(status,200);self.assertEqual(d['option']['quantity'],31200)
 def test_rejects_foreign_origin(self):self.assertEqual(self.post('scenario',{'case_id':'OPP-001'},origin='https://example.com')[0],403)
if __name__=='__main__':unittest.main()
