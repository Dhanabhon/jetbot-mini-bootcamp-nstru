"""Export slides/lecture-deck to one PDF page per slide (1920x1080), speaker notes left out.

Run from the repo root:  python3 slides/build_pdf.py
Needs Google Chrome and internet (Google Sans font and Lucide icons load from the web).
Set CHROME=/path/to/chrome if Chrome is not in the default macOS location.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "slides" / "lecture-deck"
OUT = ROOT / "docs" / "assets" / "slides" / "jetbot-mini-bootcamp-lecture.pdf"
POSTER = ROOT / "docs" / "assets" / "video" / "jetbot-mission-poster.jpg"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
LUCIDE = "https://unpkg.com/lucide-static@0.460.0/icons/{}.svg"

# The Slides viewer draws x-shape and x-icon itself; plain Chrome needs stand-ins.
PRINT_CSS = """
@page { size: 1920px 1080px; margin: 0; }
* { margin: 0; }
body > section { width: 1920px; height: 1080px; overflow: hidden; position: relative;
  break-after: page; animation: none; }
section * { animation: none !important; }
aside { display: none !important; }
x-shape { display: block; }
x-shape[kind=arrow-left]  { clip-path: polygon(40% 0,40% 25%,100% 25%,100% 75%,40% 75%,40% 100%,0 50%); }
x-shape[kind=arrow-right] { clip-path: polygon(60% 0,60% 25%,0 25%,0 75%,60% 75%,60% 100%,100% 50%); }
x-shape[kind=arrow-up]    { clip-path: polygon(0 40%,25% 40%,25% 100%,75% 100%,75% 40%,100% 40%,50% 0); }
"""


def icon_svg(match):
    name, style = match.group(1), match.group(2)
    slug = re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()
    with urllib.request.urlopen(LUCIDE.format(slug), timeout=20) as resp:
        svg = resp.read().decode("utf-8")
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    return svg.replace("<svg", '<svg style="{}"'.format(style), 1)


def build_html():
    deck = json.loads((DECK / "deck.json").read_text(encoding="utf-8"))
    face = next(iter(deck["faces"].values()))["href"]
    slides = []
    for slide_id in deck["order"]:
        html = (DECK / "slides" / "{}.html".format(slide_id)).read_text(encoding="utf-8")
        html = re.sub(r'<x-icon name="(\w+)" style="([^"]*)"></x-icon>', icon_svg, html)
        html = re.sub(r'src="/_blob/[0-9a-f]+"', 'src="{}"'.format(POSTER.as_uri()), html)
        slides.append(html)
    return (
        '<!doctype html><html lang="th"><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="{}">'
        '<link rel="stylesheet" href="{}">'
        "<style>{}</style></head><body>{}</body></html>"
    ).format(face, (DECK / "deck.css").as_uri(), PRINT_CSS, "\n".join(slides)), len(deck["order"])


def main():
    html, count = build_html()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "deck.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--virtual-time-budget=15000", "--print-to-pdf={}".format(OUT), page.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    pages = len(re.findall(rb"/Type\s*/Page[^s]", OUT.read_bytes()))
    if pages != count:
        sys.exit("expected {} pages, got {}: a slide overflowed or was split".format(count, pages))
    print("{} ({} pages, {:.1f} MB)".format(OUT.relative_to(ROOT), pages, OUT.stat().st_size / 1e6))


if __name__ == "__main__":
    main()
