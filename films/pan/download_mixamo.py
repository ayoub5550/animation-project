"""Download the PAN cast + clips from Mixamo (uses pipeline/mixamo_api.py)."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pipeline"))
import mixamo_api as mx
OUT = "/work/assets/mixamo"
# Cartoon cast (owner asked for a cartoon look 2026-09-02). Realistic alternates: Remy/Vampire/Sophie/Elizabeth.
CHARS = {"Timmy": "2312e946-b71e-4b25-b61e-4f51803aa884",
         "Goblin": "130a335c-bbdb-492f-971f-8faab0616b6e",
         "Amy": "24c3eeb4-6c47-419d-a593-f7b2948b74c7",
         "Michelle": "7f3f4e32-2b70-4c69-9a3d-0bdac6188241"}
CLIPS = {
 "Timmy": {"Crouch_Idle": ("c284106c-698e-40df-acb0-f89e764e5ba0", False),
          "Crouch_To_Stand": ("8678478a-695e-4b35-93e4-769e5bd06747", False),
          "Sneak_Walk": ("c9cd223d-b96c-11e4-a802-0aaa78deedf9", True),
          "Standing_Idle": ("c9c831cf-b96c-11e4-a802-0aaa78deedf9", False),
          "Head_Turn": ("c9c911f9-b96c-11e4-a802-0aaa78deedf9", False),
          "Kneel_Down": ("c9c8ac04-b96c-11e4-a802-0aaa78deedf9", False),
          "Kneel_Reach": ("c9c8cded-b96c-11e4-a802-0aaa78deedf9", False),
          "Reach_Out": ("c9ce7dba-b96c-11e4-a802-0aaa78deedf9", False)},
 "Goblin": {"Standing_Idle": ("c9c831cf-b96c-11e4-a802-0aaa78deedf9", False)},
 "Amy": {"Sleeping": ("c9ce6e3b-b96c-11e4-a802-0aaa78deedf9", False),
            "Waking": ("c9c82b61-b96c-11e4-a802-0aaa78deedf9", False)},
 "Michelle": {"Walking": ("c9c8b661-b96c-11e4-a802-0aaa78deedf9", True),
               "Kneel_Down": ("c9c8ac04-b96c-11e4-a802-0aaa78deedf9", False),
               "Crying": ("c9c984ee-b96c-11e4-a802-0aaa78deedf9", False)},
}
def do_export(ch, gms, name, typ, skin, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000: print("skip", path); return True
    for _ in range(3):
        try:
            mx.export(ch, gms, name, typ, skin); m = mx.monitor(ch)
            if m.get("status") == "completed":
                mx.download(m["job_result"], path); print("ok", path, os.path.getsize(path)); return True
            print("fail", name, m)
        except Exception as e:
            print("err", name, e); time.sleep(5)
    return False
def main():
    log = {}
    for cname, ch in CHARS.items():
        d = f"{OUT}/{cname}"; os.makedirs(d, exist_ok=True)
        do_export(ch, [], cname, "Character", True, f"{d}/{cname}_TPose.fbx")
        for an, (aid, inplace) in CLIPS[cname].items():
            det = mx.details(aid, ch); g = det["details"]["gms_hash"]
            params = ",".join(str(p[1]) for p in g["params"])
            gh = {"model-id": g["model-id"], "mirror": False, "trim": [0, 100], "overdrive": 0, "params": params,
                  "arm-space": 0, "inplace": bool(inplace and det["details"].get("supports_inplace"))}
            ok = do_export(ch, [gh], det["name"], "Motion", False, f"{d}/{cname}@{an}.fbx")
            log[f"{cname}/{an}"] = {"mixamo_id": aid, "name": det["name"], "desc": det.get("description"), "ok": ok}
    json.dump({"characters": CHARS, "animations": log}, open(f"{OUT}/pan_manifest.json", "w"), indent=1)
    print("DONE")
main()
