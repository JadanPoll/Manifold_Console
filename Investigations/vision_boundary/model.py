"""Bounded abstract reachability audit for Manifold's vision/Research boundary.

No external imports, device access, package installations or GUI calls.
Run: python3 Investigations/vision_boundary/model.py
"""
from collections import deque
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import csv
import json

HERE = Path(__file__).resolve().parent
NODES = {
 "U": ("Operator", "belief: unknown/trusted", "Human chooses clone, browse, launch; memory may err"),
 "R": ("Research checkout", "absent/clean/manifest", "Research source may contain an appos.json"),
 "C": ("Manifest scanner", "unknown/safe/external", "rglob discovers paths, does not execute code"),
 "H": ("Home supervisor", "idle/launching/exited", "launches explicitly selected manifest commands"),
 "D": ("Video source", "free/held/unavailable", "OpenCV owns a device/file in viewer process"),
 "P": ("Pose viewer", "off/pose/error", "single synchronous capture-infer-display loop"),
 "M": ("Native motion core", "detached/processed", "independently tested C11, not wired to P"),
 "X": ("Connect runtime", "absent", "designed, not implemented"),
}
# Every cell states classification AND reviewable reason. Direct relation,
# not reachability through intermediate components. I means inadmissible *in
# the reviewed implementation*, not physically impossible.
ROW = {
"U": ["C:self-belief update or forgetting","C:clones optional checkout","A:requests rescan","A:selects launch/stop","U:direct USB actions out of model","A:runs viewer from CLI","C:invokes make/test separately","I:no Connect user interface"],
"R": ["I:no automatic user notification","C:checkout may acquire manifest","C:external manifest found by recursive scan","I:checkout alone does not spawn apps","I:no direct camera action","I:not imported by current pose viewer","I:no automatic integration","I:no Connect implementation"],
"C": ["C:entries affect user's listing","C:directory results depend on checkout","A:rescans filesystem","A:provides manifest to Home","I:scanner never opens camera","I:package manifest is not Home appos manifest","I:scanner never runs kernels","I:no runtime Connect publication"],
"H": ["A:shows child state to operator","I:supervisor does not mutate checkout","C:manifests scanned by Home","A:launch/stop/reap children","I:no direct camera API","I:Pose package has no appos launch manifest","I:no direct motion invocation","I:no Connect routing"],
"D": ["U:device use can be externally observed","I:device cannot mutate Git checkout","I:no scanner mutation","I:no Home calls from device","C:device may deny second open","C:frames delivered if available","I:no native motion wiring","I:no Connect stream"],
"P": ["A:visual overlay observed","I:no checkout mutation","I:no scanner calls","I:current Pose viewer launched directly, not supervised","A:opens/releases capture","A:synchronous capture/infer/display loop","I:no motion-core calls","I:no pose publishing"],
"M": ["U:reports CLI test output","I:no research checkout access","I:no catalog calls","I:no supervisor calls","I:does not open video device","I:no calls into Pose viewer","A:processes caller-supplied landmarks","I:no Connect API"],
"X": ["I:no operational output","I:no checkout operations","I:no discovery operations","I:no Home operations","I:no device broker","I:no pose subscriptions","I:no motion publication","I:runtime not implemented"],
}
SUB = {
 "Acq": ["C:may capture another frame when control returns","A:passes frame to inference","I:does not invoke UI directly"],
 "Infer": ["I:no parallel acquisition callback","C:may perform sequential inference","A:returns landmarks to draw"],
 "Draw": ["C:event handling may permit later capture","I:no inference API calls from draw","A:draws and pumps UI events"],
}
STOP = {
 "U": "Stop: user observations and fallible belief suffice; cognition not modeled.",
 "R": "Stop: only whether checkout contains a manifest matters; Git internals omitted.",
 "C": "Stop: rglob path admission is the investigated boundary; JSON parsing abstracted.",
 "H": "Stop: launch selected command is modeled, kernel scheduling and child trees omitted.",
 "D": "Stop: device open/held is enough; USB timing and permissions unresolved.",
 "P": "Refine: synchronous acquisition -> inference -> display can affect temporal independence.",
 "M": "Stop: C11 standalone library has no current pose integration; geometry internals irrelevant here.",
 "X": "Stop: no executing Connect runtime exists; proposed ports are not assumed real.",
}
@dataclass(frozen=True)
class State:
    research: str = "absent"
    catalog: str = "unknown"
    belief: str = "unknown"  # B_operator; 'trusted' can be mistaken
    app: str = "off"         # off, pose, unreviewed, error
    device: str = "free"
    inference: str = "idle"
    view: str = "idle"
    age: int = 0            # logical delay ticks, capped at 2

def successors(s, exclude_research):
    if s.research == "absent":
        yield "clone:benign", replace(s, research="clean")
        yield "clone:contains_appos_manifest", replace(s, research="manifest")
    expected = ("external" if s.research == "manifest" and not exclude_research else "safe")
    if s.research != "absent" and s.catalog != expected:
        yield "rescan_catalog", replace(s, catalog=expected)
    if s.catalog != "unknown" and s.belief != "trusted":
        yield "user_sees_listing_as_trusted", replace(s, belief="trusted")
    if s.belief == "trusted":
        yield "user_forgets", replace(s, belief="unknown")
    if s.catalog == "external" and s.belief == "trusted" and s.app == "off":
        yield "user_launches_external_manifest", replace(s, app="unreviewed")
    if s.app == "off":
        # Command line Pose launch: alternatives represent host environment.
        yield "cli_pose:available", replace(s, app="pose", device="held", view="ready")
        yield "cli_pose:missing_dependency", replace(s, app="error", view="idle")
    elif s.app == "error":
        yield "user_retries", replace(s, app="off")
    elif s.app == "unreviewed":
        yield "external_process_exits", replace(s, app="off")
    elif s.app == "pose":
        if s.inference == "idle":
            yield "next_frame_begin_inference", replace(s, inference="busy", view="blocked", age=0)
        else:
            yield "inference_completes_and_displays", replace(s, inference="idle", view="ready", age=0)
            if s.age < 2:
                yield "inference_delay_tick", replace(s, age=s.age+1)
        yield "user_stops_pose", replace(s, app="off", device="free",
                                         inference="idle", view="idle", age=0)
        yield "capture_or_model_error", replace(s, app="error", device="free",
                                                inference="idle", view="idle", age=0)

def fail(s):
    result = []
    if s.app == "unreviewed":
        result.append("F1_unreviewed_manifest_executed")
    if s.app == "pose" and s.inference == "busy" and s.age >= 2:
        result.append("F2_blocking_inference_over_budget")
    return result

def bfs(exclude_research, limit=100000):
    start = State()
    queue = deque([start])
    prev = {start: None}
    paths = {}
    edges = 0
    depth = {start:0}
    maxdepth = 0
    while queue:
        s = queue.popleft()
        for label, ns in successors(s, exclude_research):
            edges += 1
            if ns in prev:
                continue
            if len(prev) >= limit:
                raise RuntimeError("state limit reached: exploration incomplete")
            prev[ns] = (s, label)
            depth[ns] = depth[s]+1
            maxdepth=max(maxdepth,depth[ns])
            queue.append(ns)
            for failure in fail(ns):
                if failure not in paths:
                    seq = []
                    cur = ns
                    while prev[cur] is not None:
                        parent, event = prev[cur]
                        seq.append({"event":event,"state":asdict(cur)})
                        cur = parent
                    paths[failure] = list(reversed(seq))
    return {"states":len(prev),"edges_checked":edges,"max_shortest_depth":maxdepth,
            "bound":limit,"failures":paths}

def matrix(path, labels, rows):
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.writer(handle)
        writer.writerow(["from/to",*labels])
        for name in labels:
            cells=rows[name]
            assert len(cells)==len(labels), name
            assert all(c[:2] in ("A:","C:","I:","U:") and len(c)>5 for c in cells)
            writer.writerow([name,*cells])

def main():
    HERE.mkdir(parents=True, exist_ok=True)
    matrix(HERE/"matrix_depth0.csv",list(NODES),ROW)
    matrix(HERE/"matrix_pose_depth1.csv",list(SUB),SUB)
    legacy = bfs(False)
    mitigated = bfs(True)
    report = {"model":"finite, nondeterministic, abstract only",
              "depth0_nodes":NODES,"refinement_or_stop":STOP,
              "depth1_pose_nodes":["Acq","Infer","Draw"],
              "legacy":legacy,"with_external_exclusion":mitigated,
              "constraints":{
                "F1":"Proposed Research inspection boundary: external checkout manifests must not become Home-executable",
                "F2":"Proposed temporal independence: a slow pose inference must not stall user-facing viewer or capture; 2 symbolic delay ticks, not milliseconds"},
              "limitations":["No software/USB APIs executed","No Connect runtime exists",
                "Pose is CLI-only; not Home-launchable today",
                "Device exclusivity and kernel scheduling not explored",
                "Unresolved physical relations excluded from proven conclusions",
                "Inferred events are abstract possibilities, not observed failures"]}
    (HERE/"coverage_and_traces.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({name:{"states":r["states"],"edges":r["edges_checked"],
                             "max_shortest_depth":r["max_shortest_depth"],
                             "failures":{k:len(v) for k,v in r["failures"].items()}}
                      for name,r in [("before",legacy),("after",mitigated)]},indent=2))
if __name__ == "__main__":
    main()
