import unittest
from browser import read_catalog, search, agent_context

class CatalogTests(unittest.TestCase):
    def test_load(self):
        items=read_catalog()
        self.assertGreaterEqual(len(items),4)
        self.assertEqual(len({c["id"] for c in items}),len(items))
    def test_status(self):
        items=read_catalog()
        self.assertEqual([c["id"] for c in search(items,status="idea")],["vision.multi_camera"])
    def test_search(self):
        items=read_catalog()
        self.assertTrue(any(c["id"]=="camera.kinect_depth" for c in search(items,"kinect")))
    def test_context(self):
        c=read_catalog()[0]
        self.assertEqual(__import__("json").loads(agent_context(c))["id"],c["id"])

if __name__=="__main__":
    unittest.main()
