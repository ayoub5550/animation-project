"""Poly Haven downloader (CC0). Usage: python polyhaven.py model <id> [res] | hdri <id> [res] | texture <id> [res]
Files land in /work/assets/polyhaven/<type>/<id>/ ; models as glTF with textures."""
import httpx, os, sys, json
H = {"User-Agent": "Mozilla/5.0"}
ROOT = "/work/assets/polyhaven"
def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with httpx.stream("GET", url, headers=H, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for ch in r.iter_bytes(): f.write(ch)
    return path
def files(aid): return httpx.get(f"https://api.polyhaven.com/files/{aid}", headers=H, timeout=60).json()
def model(aid, res="2k"):
    f = files(aid)["gltf"]; res = res if res in f else sorted(f)[0]
    entry = f[res]["gltf"]; d = f"{ROOT}/models/{aid}"
    main = get(entry["url"], f"{d}/{aid}.gltf")
    for rel, inc in entry.get("include", {}).items(): get(inc["url"], f"{d}/{rel}")
    print("MODEL", aid, res, main); return main
def hdri(aid, res="2k"):
    f = files(aid)["hdri"]; res = res if res in f else sorted(f)[0]
    p = get(f[res]["hdr"]["url"], f"{ROOT}/hdris/{aid}_{res}.hdr"); print("HDRI", aid, p); return p
def texture(aid, res="2k"):
    f = files(aid); d = f"{ROOT}/textures/{aid}"; out = {}
    for m in ["Diffuse", "nor_gl", "Rough", "Displacement", "AO"]:
        if m in f:
            r = res if res in f[m] else sorted(f[m])[0]
            fmt = "jpg" if "jpg" in f[m][r] else sorted(f[m][r])[0]
            out[m] = get(f[m][r][fmt]["url"], f"{d}/{aid}_{m}.{fmt}")
    print("TEXTURE", aid, list(out)); return out
if __name__ == "__main__":
    kind, aid = sys.argv[1], sys.argv[2]; res = sys.argv[3] if len(sys.argv) > 3 else "2k"
    {"model": model, "hdri": hdri, "texture": texture}[kind](aid, res)
