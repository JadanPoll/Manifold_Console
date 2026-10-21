import unittest
from AppOS.Latent.subscriptions import Range,Scheduler

class Tests(unittest.TestCase):
    def test_profiles(self):
        clock=[0.0]
        fired=[]
        s=Scheduler(clock=lambda:clock[0])
        s.subscribe("sprites",lambda:fired.append(clock[0]),Range(15,30,60),Range(1,2,10),Range(1,1,5))
        s.tick();self.assertEqual(len(fired),1)
        clock[0]=.02;s.tick();self.assertEqual(len(fired),1)
        clock[0]=.04;s.tick();self.assertEqual(len(fired),2)
        s.set_profile("background")
        self.assertEqual(s.inspect()[0]["target_hz"],2)
        clock[0]=.10;s.tick();self.assertEqual(len(fired),2)
        clock[0]=.55;s.tick();self.assertEqual(len(fired),3)
    def test_reject(self):
        with self.assertRaises(ValueError): Range(5,3,10)
        with self.assertRaises(ValueError): Range(1,1,float("nan"))
        with self.assertRaises(ValueError): Scheduler().set_profile("turbo")

if __name__=="__main__":unittest.main()
