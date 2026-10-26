"""
Refreshes the Dream Inventory data.

Downloads every Valorant weapon skin from the community VALORANT-API,
shrinks each picture, packs them into one small picture sheet per weapon
and writes a skin list. Everything goes into the top folder of the repository, which is
what your website serves. The GitHub workflow in this repository runs
this script once a day, so new skins appear without any work from you.

You can also run it yourself:  pip install pillow  then  python update_site.py
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is missing. Run:  pip install pillow")

API = "https://valorant-api.com/v1"
OUT = "."
CW, CH, COLS = 288, 120, 6          # one picture cell, and cells per row
TIER_BY_NAME = {"Select": "S", "Deluxe": "D", "Premium": "P", "Exclusive": "E", "Ultra": "U"}
GROUP_BY_CAT = {"Sidearm": "Sidearms", "SMG": "SMGs", "Shotgun": "Shotguns", "Rifle": "Rifles",
                "Sniper": "Sniper Rifles", "Heavy": "Machine Guns", "Melee": "Melee"}


def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dream-inventory-updater"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(1 + 2 * i)
    raise last


def get_json(url, get=fetch):
    return json.loads(get(url).decode("utf-8"))["data"]


def pick_image_url(s):
    if s.get("displayIcon"):
        return s["displayIcon"]
    for lv in s.get("levels") or []:
        if lv.get("displayIcon"):
            return lv["displayIcon"]
    for ch in s.get("chromas") or []:
        if ch.get("fullRender"):
            return ch["fullRender"]
    return None


def make_cell(raw):
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    box = im.getbbox()
    if box:
        im = im.crop(box)
    k = min(CW / im.width, CH / im.height, 1.0)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def build(weapons, tiers, out_dir=OUT, get=fetch):
    tier_code = {t["uuid"]: TIER_BY_NAME.get(t["devName"], "C") for t in tiers}
    atlas_dir = out_dir
    os.makedirs(atlas_dir, exist_ok=True)
    catalog = {"cols": COLS, "w": {}, "meta": {}}
    digest = hashlib.sha1()
    keep, total, failed = set(), 0, 0

    for w in sorted(weapons, key=lambda x: x["displayName"]):
        wid = w["displayName"].lower().replace(" ", "")
        skins = []
        for s in w.get("skins") or []:
            name = s.get("displayName") or ""
            if not s.get("contentTierUuid") or name.startswith("Standard ") or name.startswith("Random Favorite"):
                continue
            skins.append((name, tier_code.get(s["contentTierUuid"], "C"), pick_image_url(s)))
        skins.sort(key=lambda x: x[0].lower())
        cat = str(w.get("category") or "").split("::")[-1]
        catalog["meta"][wid] = {"n": w["displayName"], "g": GROUP_BY_CAT.get(cat, "Other")}
        rows = (len(skins) + COLS - 1) // COLS
        catalog["w"][wid] = {"rows": rows, "skins": [[n, t] for n, t, _ in skins]}
        if not skins:
            continue

        def load(i):
            url = skins[i][2]
            if not url:
                return None
            try:
                return make_cell(get(url))
            except Exception as e:
                print("  picture failed:", skins[i][0], e)
                return None

        with ThreadPoolExecutor(max_workers=8) as ex:
            cells = list(ex.map(load, range(len(skins))))
        sheet = Image.new("RGBA", (COLS * CW, rows * CH), (0, 0, 0, 0))
        for i, im in enumerate(cells):
            total += 1
            if im is None:
                failed += 1
                continue
            x = (i % COLS) * CW + (CW - im.width) // 2
            y = (i // COLS) * CH + (CH - im.height) // 2
            sheet.paste(im, (x, y), im)
        path = os.path.join(atlas_dir, wid + ".webp")
        sheet.save(path, "WEBP", quality=74, method=3)
        keep.add(wid + ".webp")
        with open(path, "rb") as f:
            digest.update(f.read())
        print(f"  {w['displayName']}: {len(skins)} skins")

    if total and failed / total > 0.2:
        sys.exit(f"Too many pictures failed ({failed} of {total}). Keeping the old data.")

    digest.update(json.dumps(catalog, sort_keys=True).encode("utf-8"))
    catalog["v"] = digest.hexdigest()[:10]       # changes only when the content changes
    for fn in os.listdir(atlas_dir):             # drop sheets of weapons that no longer exist
        if fn.endswith(".webp") and fn not in keep:
            os.remove(os.path.join(atlas_dir, fn))
    with open(os.path.join(out_dir, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    n = sum(len(x["skins"]) for x in catalog["w"].values())
    print(f"Done: {n} skins, version {catalog['v']}.")
    return catalog


def main():
    print("Fetching weapons and tiers...")
    weapons = get_json(API + "/weapons")
    tiers = get_json(API + "/contenttiers")
    if not weapons or not tiers:
        sys.exit("The API returned no data. Keeping the old data.")
    build(weapons, tiers)


if __name__ == "__main__":
    main()
