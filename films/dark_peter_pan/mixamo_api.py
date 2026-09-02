"""Mixamo API helper via httpx with bearer token."""
import httpx, json, time
import os
TOK=os.environ.get("MIXAMO_TOKEN") or open(os.environ.get("MIXAMO_TOKEN_FILE","/work/temp/mx/token.txt")).read().strip()
H={"Authorization": f"Bearer {TOK}", "X-Api-Key": "mixamo2", "Accept":"application/json","Content-Type":"application/json",
   "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128 Safari/537.36","Origin":"https://www.mixamo.com","Referer":"https://www.mixamo.com/"}
BASE="https://www.mixamo.com/api/v1"
c=httpx.Client(headers=H, timeout=60)
def search(q, typ="Motion", limit=40):
    r=c.get(f"{BASE}/products", params={"page":1,"limit":limit,"order":"","type":typ,"query":q}); r.raise_for_status(); return r.json()
def details(pid, ch):
    r=c.get(f"{BASE}/products/{pid}", params={"similar":0,"character_id":ch}); r.raise_for_status(); return r.json()
def export(ch, gms, name, typ, skin):
    body={"gms_hash":gms,"preferences":{"format":"fbx7_2019","skin":"true" if skin else "false","fps":"30","reducekf":"0"},"character_id":ch,"type":typ,"product_name":name}
    r=c.post(f"{BASE}/animations/export", json=body); r.raise_for_status(); return r.json()
def monitor(ch, tries=60):
    for _ in range(tries):
        time.sleep(2.5)
        r=c.get(f"{BASE}/characters/{ch}/monitor"); m=r.json()
        if m.get("status") in ("completed","failed"): return m
    return {"status":"timeout"}
def download(url, path):
    with httpx.stream("GET", url, timeout=120) as r:
        r.raise_for_status()
        with open(path,"wb") as f:
            for ch in r.iter_bytes(): f.write(ch)
if __name__=="__main__":
    import sys
    for q in sys.argv[1:]:
        b=search(q); print("###", q, b["pagination"]["num_results"])
        for p in b["results"][:14]: print(" ", p["id"], "|", p["name"], "|", p.get("description","")[:55])
