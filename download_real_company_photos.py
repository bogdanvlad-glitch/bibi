#!/usr/bin/env python3
import html
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

API = "https://commons.wikimedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "BusinessmanTycoonRealPhotos/1.0"})

ROOT = Path("company_realistic_assets")
PLAN = Path("queries.json")

MIN_W = 1000
MIN_H = 600
NEEDED = 5

def clean_text(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

def search_files(query: str, limit: int = 20):
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo|info",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": 1600,
        "inprop": "url",
    }
    r = SESSION.get(API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    pages = list((data.get("query", {}) or {}).get("pages", {}).values())
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        ext = ii.get("extmetadata") or {}
        desc = clean_text(ext.get("ImageDescription", {}).get("value", ""))
        artist = clean_text(ext.get("Artist", {}).get("value", ""))
        lic = clean_text(ext.get("LicenseShortName", {}).get("value", ""))
        out.append({
            "title": p.get("title", ""),
            "url": ii.get("thumburl") or ii.get("url"),
            "source_url": ii.get("descriptionurl") or p.get("fullurl"),
            "mime": ii.get("mime", ""),
            "width": ii.get("thumbwidth") or ii.get("width") or 0,
            "height": ii.get("thumbheight") or ii.get("height") or 0,
            "desc": desc,
            "artist": artist,
            "license": lic,
            "blob": " ".join([clean_text(p.get("title","")), desc, artist, lic]),
        })
    return out

def good(item, include, exclude):
    if not item["url"]:
        return False
    if not item["mime"].startswith("image/"):
        return False
    if item["width"] < MIN_W or item["height"] < MIN_H:
        return False
    text = item["blob"]
    if any(bad in text for bad in exclude):
        return False
    hits = sum(1 for token in include if token in text)
    return hits >= max(1, min(2, len(include)//3))

def safe_get(url: str, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    r = SESSION.get(url, timeout=60, stream=True)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(1 << 15):
            if chunk:
                f.write(chunk)

def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    ROOT.mkdir(exist_ok=True)
    credits = {}
    downloaded_titles = set()

    for company, upgrades in plan.items():
        credits[company] = {}
        for upgrade, cfg in upgrades.items():
            folder = ROOT / company / upgrade
            folder.mkdir(parents=True, exist_ok=True)
            found = []
            seen_urls = set()
            for q in cfg["queries"]:
                results = search_files(q, limit=25)
                results.sort(key=lambda x: (x["width"] * x["height"]), reverse=True)
                for item in results:
                    if len(found) >= NEEDED:
                        break
                    if item["title"] in downloaded_titles or item["url"] in seen_urls:
                        continue
                    if not good(item, cfg["include"], cfg["exclude"]):
                        continue
                    found.append(item)
                    seen_urls.add(item["url"])
                    downloaded_titles.add(item["title"])
                if len(found) >= NEEDED:
                    break

            if len(found) < NEEDED:
                # fallback: relax title uniqueness, keep same category relevance
                for q in cfg["queries"]:
                    results = search_files(q, limit=40)
                    results.sort(key=lambda x: (x["width"] * x["height"]), reverse=True)
                    for item in results:
                        if len(found) >= NEEDED:
                            break
                        if item["url"] in seen_urls:
                            continue
                        if not good(item, cfg["include"], cfg["exclude"]):
                            continue
                        found.append(item)
                        seen_urls.add(item["url"])
                    if len(found) >= NEEDED:
                        break

            credits[company][upgrade] = []
            for idx, item in enumerate(found[:NEEDED], start=1):
                out = folder / f"{upgrade}_{idx:02d}.jpg"
                safe_get(item["url"], out)
                credits[company][upgrade].append({
                    "file": out.name,
                    "title": item["title"],
                    "source_url": item["source_url"],
                    "license": item["license"] or "see source page",
                })
                print(f"[OK] {company}/{upgrade}/{out.name}")

            if len(found) < NEEDED:
                print(f"[WARN] {company}/{upgrade}: only {len(found)} image(s) found.")

            time.sleep(1.0)

    (ROOT / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Done.")
    print("Output:", ROOT.resolve())

if __name__ == "__main__":
    main()
