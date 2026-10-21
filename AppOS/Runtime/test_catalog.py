import tempfile
import json
import unittest
from pathlib import Path
from AppOS.Runtime.catalog import discover

class CatalogTests(unittest.TestCase):
    def test_manifest_discovery_and_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            good=root/"good"
            good.mkdir()
            (good/"appos.json").write_text(json.dumps({"schema_version":1,"id":"demo","name":"Demo","entry":{"command":["python3","main.py"]}}))
            bad=root/"bad"
            bad.mkdir()
            (bad/"appos.json").write_text('{"schema_version":2}')
            apps=discover(root)
            self.assertEqual(len(apps),1)
            self.assertEqual(apps[0]["id"],"demo")

if __name__=="__main__": unittest.main()
