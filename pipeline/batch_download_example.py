import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import mixamo_api as mx
OUT="/work/assets/mixamo"
CHARS={
 "Survivor":   "52dcdacb-b43e-4efc-ab6d-9d2d6e09bc95",
 "Zombiegirl": "2f8e576f-f69d-453e-830e-969a2f0217ea",
 "Copzombie":  "3d9daeb8-c2d5-45ce-b835-7cd403c72fc7",
 "Warzombie":  "3576fd60-beef-49ec-a3d0-f93231f4fc29",
 "Romero":     "576b18a3-2e3e-4f50-b665-cbca337e0757",
}
ZOMBIE_ANIMS={ # name: (id, inplace)
 "Idle":        ("c9cbd649-b96c-11e4-a802-0aaa78deedf9", False),
 "Idle_Twitch": ("c9c6b3ad-b96c-11e4-a802-0aaa78deedf9", False),
 "Walk":        ("c9cbd4d9-b96c-11e4-a802-0aaa78deedf9", True),
 "Run":         ("c9c6b0ab-b96c-11e4-a802-0aaa78deedf9", True),
 "Attack":      ("c9cbd7ad-b96c-11e4-a802-0aaa78deedf9", False),
 "Attack2":     ("c9c68115-b96c-11e4-a802-0aaa78deedf9", False),
 "Scream":      ("c9ccbc37-b96c-11e4-a802-0aaa78deedf9", False),
 "Hit":         ("c9c68a0f-b96c-11e4-a802-0aaa78deedf9", False),
 "Hit_Stumble": ("c9c68ad5-b96c-11e4-a802-0aaa78deedf9", False),
 "Death_Back":  ("c9cbda5a-b96c-11e4-a802-0aaa78deedf9", False),
 "Death_Front": ("c9cc240a-b96c-11e4-a802-0aaa78deedf9", False),
 "StandUp":     ("c9c6b165-b96c-11e4-a802-0aaa78deedf9", False),
 "Crawl":       ("c9cbee0c-b96c-11e4-a802-0aaa78deedf9", True),
}
PLAYER_ANIMS={
 "Idle":              ("c9c972d1-b96c-11e4-a802-0aaa78deedf9", False),
 "Pistol_Idle":       ("c9cdb599-b96c-11e4-a802-0aaa78deedf9", False),
 "Pistol_Walk":       ("c9cdb8f0-b96c-11e4-a802-0aaa78deedf9", True),
 "Pistol_Walk_Back":  ("c9cdba81-b96c-11e4-a802-0aaa78deedf9", True),
 "Pistol_Strafe_L":   ("c9cdbb48-b96c-11e4-a802-0aaa78deedf9", True),
 "Pistol_Strafe_R":   ("c9cdbc0b-b96c-11e4-a802-0aaa78deedf9", True),
 "Pistol_Run":        ("c9cdb75a-b96c-11e4-a802-0aaa78deedf9", True),
 "Run":               ("c9c99715-b96c-11e4-a802-0aaa78deedf9", True),
 "Shoot":             ("c9c81565-b96c-11e4-a802-0aaa78deedf9", False),
 "Reload":            ("c9c646a9-b96c-11e4-a802-0aaa78deedf9", True),
 "Hit":               ("c9c6bc60-b96c-11e4-a802-0aaa78deedf9", False),
 "Death":             ("c9c899a0-b96c-11e4-a802-0aaa78deedf9", False),
 "Death_Back":        ("e13a58d8-0104-45a5-9837-03fc3c307632", False),
}
def do_export(ch, gms, name, typ, skin, path):
    if os.path.exists(path) and os.path.getsize(path)>1000: print("skip", path); return True
    for attempt in range(3):
        try:
            mx.export(ch, gms, name, typ, skin)
            m=mx.monitor(ch)
            if m.get("status")=="completed":
                mx.download(m["job_result"], path); print("ok", path, os.path.getsize(path)); return True
            print("fail", name, m)
        except Exception as e:
            print("err", name, e); time.sleep(5)
    return False
def main():
    log={}
    for cname, ch in CHARS.items():
        d=f"{OUT}/{cname}"; os.makedirs(d, exist_ok=True)
        # T-pose skinned character
        do_export(ch, [], cname, "Character", True, f"{d}/{cname}_TPose.fbx")
        anims = PLAYER_ANIMS if cname=="Survivor" else ZOMBIE_ANIMS
        for an,(aid,inplace) in anims.items():
            det=mx.details(aid, ch); g=det["details"]["gms_hash"]
            params=",".join(str(p[1]) for p in g["params"])
            gh={"model-id":g["model-id"],"mirror":False,"trim":[0,100],"overdrive":0,"params":params,"arm-space":0,"inplace":bool(inplace and det["details"].get("supports_inplace"))}
            ok=do_export(ch, [gh], det["name"], "Motion", False, f"{d}/{cname}@{an}.fbx")
            log[f"{cname}/{an}"]={"mixamo_id":aid,"name":det["name"],"desc":det.get("description"),"ok":ok}
    json.dump({"characters":CHARS,"animations":log}, open(f"{OUT}/manifest.json","w"), indent=1)
    print("DONE")
main()
