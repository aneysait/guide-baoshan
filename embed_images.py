#!/usr/bin/env python3
"""Remplit les emplacements photo du guide avec les fichiers de images/.

Chaque emplacement est un <div class="slot" data-img="nom.jpg">. Si images/nom.jpg
existe, il est redimensionné, recompressé et incrusté en base64 dans le HTML.
Relancer après chaque nouvel ajout dans images/ ; c'est idempotent.
"""
import base64, io, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "guide-baoshan.html")
IMGDIR = os.path.join(ROOT, "images")
MAX_W = 1200          # largeur max : ~150 dpi sur une demi-page A4
JPEG_QUALITY = 82

def encode(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGB") if not path.lower().endswith(".png") else im.convert("RGBA")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if path.lower().endswith(".png"):
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"
    else:
        im.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        mime = "image/jpeg"
    return mime, base64.b64encode(buf.getvalue()).decode(), len(buf.getvalue())

def main():
    html = open(HTML, encoding="utf-8").read()
    slots = re.findall(r'<div class="slot([^"]*)" data-img="([^"]+)">.*?</div>', html, re.S)
    if not slots:
        print("aucun emplacement libre — tout est déjà rempli ?")
    filled = 0
    for cls, name in slots:
        path = os.path.join(IMGDIR, name)
        if not os.path.exists(path):
            print(f"  … {name} : en attente")
            continue
        mime, b64, size = encode(path)
        pattern = re.compile(r'<div class="slot' + re.escape(cls) + r'" data-img="' + re.escape(name) + r'">.*?</div>', re.S)
        repl = (f'<div class="slot{cls} filled" data-img="{name}">'
                f'<img src="data:{mime};base64,{b64}" alt=""></div>')
        html = pattern.sub(lambda m: repl, html, count=1)
        filled += 1
        print(f"  ✓ {name} : {size // 1024} Ko incrustés")
    open(HTML, "w", encoding="utf-8").write(html)
    print(f"{filled} image(s) incrustée(s) · guide : {len(html) // 1024} Ko")

if __name__ == "__main__":
    main()
