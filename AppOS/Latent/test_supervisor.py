import unittest
from AppOS.Latent.supervisor import host_memory, process_rss, Supervisor
class Tests(unittest.TestCase):
    def test_host_memory_shape(self):
        available,total=host_memory()
        self.assertTrue(available is None or 0 <= available <= total)
    def test_unknown_process(self):
        self.assertIsNone(process_rss(999999999))
    def test_empty(self):
        self.assertEqual(Supervisor().snapshots(), [])
if __name__=="__main__":
    unittest.main()
