"""Download Poly Haven (CC0) assets by id — models as glTF, textures as JPG maps, HDRIs as .hdr.

Usage:
  python polyhaven_download.py model  GothicBed_01 WoodenChair_01 [--res 2k]
  python polyhaven_download.py texture old_wood_floor decrepit_wallpaper [--res 2k]
  python polyhaven_download.py hdri   rogland_moonlit_night [--res 2k]
Output: $PH_OUT (default /work/assets/polyhaven)/<id>/... for models,
        <id>_{Diffuse,Rough,nor_gl}.jpg for textures, <id>_<res>.hdr for HDRIs.
API: https://api.polyhaven.com/files/<id> (no key needed). Skips files already present.
"""
import json, os, sys, urllib.request, concurrent.futures as cf

OUT = os.environ.get("PH_OUT", "/work/assets/polyhaven")
UA = {"User-Agent": "Mozilla/5.0"}


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r, open(path, "wb") as f:
                f.write(r.read())
            return path
        except Exception as e:  # noqa
            err = e
    raise RuntimeError(f"{url}: {err}")


def model(aid, res="2k"):
    files = get_json(f"https://api.polyhaven.com/files/{aid}")
    fmt = "gltf" if "gltf" in files else "fbx"  # a few models (e.g. decorative_book_set_01) have no glTF
    g = files[fmt].get(res) or files[fmt][sorted(files[fmt])[0]]
    g = g[fmt]
    d = f"{OUT}/{aid}"
    jobs = [(g["url"], f"{d}/{aid}.{fmt}")] + [(v["url"], f"{d}/{k}") for k, v in g["include"].items()]
    with cf.ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda j: fetch(*j), jobs))
    print(f"model {aid}: {len(jobs)} files -> {d}/{aid}.{fmt}")


def texture(aid, res="2k"):
    files = get_json(f"https://api.polyhaven.com/files/{aid}")
    got = []
    for m in ("Diffuse", "Rough", "nor_gl", "Displacement", "AO"):
        if m in files and res in files[m] and "jpg" in files[m][res]:
            fetch(files[m][res]["jpg"]["url"], f"{OUT}/{aid}_{m}.jpg"); got.append(m)
    print(f"texture {aid}: {got}")


def hdri(aid, res="2k"):
    files = get_json(f"https://api.polyhaven.com/files/{aid}")
    fetch(files["hdri"][res]["hdr"]["url"], f"{OUT}/{aid}_{res}.hdr")
    print(f"hdri {aid}_{res}.hdr")


def main():
    args = sys.argv[1:]
    res = "2k"
    if "--res" in args:
        i = args.index("--res"); res = args[i + 1]; del args[i:i + 2]
    kind, ids = args[0], args[1:]
    fn = {"model": model, "texture": texture, "hdri": hdri}[kind]
    for aid in ids:
        fn(aid, res)


if __name__ == "__main__":
    main()
