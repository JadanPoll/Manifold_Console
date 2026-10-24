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


    def test_external_research_checkout_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "Applications" / "approved"
            outside = root / "Playroom" / "Research_Campus" / "external" / "unreviewed"
            for folder, ident in ((good, "approved"), (outside, "unreviewed")):
                folder.mkdir(parents=True)
                (folder / "appos.json").write_text(json.dumps({
                    "schema_version": 1, "id": ident, "name": ident,
                    "entry": {"command": ["python3", "main.py"]}
                }))
            self.assertEqual([app["id"] for app in discover(root)], ["approved"])

    def test_external_name_outside_research_remains_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Applications" / "external"
            folder.mkdir(parents=True)
            (folder / "appos.json").write_text(json.dumps({
                "schema_version": 1, "id": "app", "name": "App",
                "entry": {"command": ["python3", "main.py"]}
            }))
            self.assertEqual([app["id"] for app in discover(root)], ["app"])

if __name__=="__main__": unittest.main()
