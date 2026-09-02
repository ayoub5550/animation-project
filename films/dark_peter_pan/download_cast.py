"""Download the Dark Peter Pan cast + clips from Mixamo (T-pose skinned + clips without skin)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import mixamo_api as mx
OUT = "/work/assets/mixamo"
CHARS = {
 "Bryce": "e90a6228-9937-4a24-83f7-886adcfb0a0a",   # PETER
 "Lewis": "bb7d74a1-ffe3-4fb5-b6b5-48c5fecc9b4e",   # LOST BOY
 "Kate":  "aba68976-90b0-4c6d-9f96-922dd1644be5",   # WENDY (adult)
}
CLIPS = {  # name: (id, inplace, which characters)
 "Breathing_Idle":   ("c9c6d0d5-b96c-11e4-a802-0aaa78deedf9", False, ["Bryce","Lewis","Kate"]),
 "Standing_Idle":    ("c9c972d1-b96c-11e4-a802-0aaa78deedf9", False, ["Bryce","Kate"]),
 "Looking_Behind":   ("c9c8c433-b96c-11e4-a802-0aaa78deedf9", False, ["Bryce"]),
 "Kneeling_Prayer":  ("c9c6a211-b96c-11e4-a802-0aaa78deedf9", False, ["Bryce"]),
 "Kneeling_Idle":    ("c9cd9c47-b96c-11e4-a802-0aaa78deedf9", False, ["Bryce"]),
 "Careful_Walk":     ("c9c7fda5-b96c-11e4-a802-0aaa78deedf9", True,  ["Bryce"]),
 "Standard_Walk":    ("c9ccc2e9-b96c-11e4-a802-0aaa78deedf9", True,  ["Bryce","Lewis"]),
 "Run_Look_Back":    ("c9ce7839-b96c-11e4-a802-0aaa78deedf9", True,  ["Lewis"]),
 "Running":          ("c9c99715-b96c-11e4-a802-0aaa78deedf9", True,  ["Lewis"]),
 "Look_Around_Nerv": ("c9c8f860-b96c-11e4-a802-0aaa78deedf9", False, ["Kate","Lewis"]),
 "Nervous_Look_Loop":("c9c900c8-b96c-11e4-a802-0aaa78deedf9", False, ["Kate"]),
}
def do_export(ch, gms, name, typ, skin, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000: print("skip", path); return True
    for attempt in range(3):
        try:
            mx.export(ch, gms, name, typ, skin)
            m = mx.monitor(ch)
            if m.get("status") == "completed":
                mx.download(m["job_result"], path); print("ok", path, os.path.getsize(path), flush=True); return True
            print("fail", name, m, flush=True)
        except Exception as e:
            print("err", name, e, flush=True); time.sleep(5)
    return False
def main():
    log = {}
    for cname, ch in CHARS.items():
        d = f"{OUT}/{cname}"; os.makedirs(d, exist_ok=True)
        do_export(ch, [], cname, "Character", True, f"{d}/{cname}_TPose.fbx")
        for an, (aid, inplace, who) in CLIPS.items():
            if cname not in who: continue
            det = mx.details(aid, ch); g = det["details"]["gms_hash"]
            params = ",".join(str(p[1]) for p in g["params"])
            gh = {"model-id": g["model-id"], "mirror": False, "trim": [0, 100], "overdrive": 0, "params": params,
                  "arm-space": 0, "inplace": bool(inplace and det["details"].get("supports_inplace"))}
            ok = do_export(ch, [gh], det["name"], "Motion", False, f"{d}/{cname}@{an}.fbx")
            log[f"{cname}/{an}"] = {"mixamo_id": aid, "name": det["name"], "desc": det.get("description"), "ok": ok}
    json.dump({"characters": CHARS, "animations": log}, open(f"{OUT}/manifest.json", "w"), indent=1)
    print("DONE")
main()
