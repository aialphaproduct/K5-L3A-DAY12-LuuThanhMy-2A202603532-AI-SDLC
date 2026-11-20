import json, tempfile, unittest
from simulation import run_headless
class ContractTests(unittest.TestCase):
    def test_deterministic(self):
        a=run_headless(7,120,10); b=run_headless(7,120,10); self.assertEqual(a,b)
    def test_pickup_event(self):
        with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:
            json.dump({'player':{'pos':[0,0,0]},'random_motes':False,'random_shades':False,'motes':[[0,0,0]],'lanterns':[]},f); p=f.name
        lines=run_headless(1,1,1,p); self.assertTrue(any('mote_picked' in x for x in lines))
if __name__=='__main__': unittest.main()
