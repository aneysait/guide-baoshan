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
MAX_W = 900           # largeur max : lisible à l'écran et correct à l'impression
JPEG_QUALITY = 76

def encode(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGB") if not path.lower().endswith(".png") else im.convert("RGBA")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if "qr" in os.path.basename(path).lower():
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"
    else:
        im.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        mime = "image/jpeg"
    return mime, base64.b64encode(buf.getvalue()).decode(), len(buf.getvalue())

def main():
    html = open(HTML, encoding="utf-8").read()
    slots = re.findall(r'<(?:div|span) class="slot([^"]*)" data-img="([^"]+)"([^>]*)>.*?</(?:div|span)>', html, re.S)
    if not slots:
        print("aucun emplacement libre — tout est déjà rempli ?")
    filled = 0
    for cls, name, extra in slots:
        path = os.path.join(IMGDIR, name)
        if not os.path.exists(path):
            print(f"  … {name} : en attente")
            continue
        mime, b64, size = encode(path)
        pattern = re.compile(r'<(div|span) class="slot' + re.escape(cls) + r'" data-img="' + re.escape(name) + r'"' + re.escape(extra) + r'>.*?</(?:div|span)>', re.S)
        def _sub(m):
            tag = m.group(1)
            return (f'<{tag} class="slot{cls} filled" data-img="{name}"{extra}>'
                    f'<img src="data:{mime};base64,{b64}" alt=""></{tag}>')
        html = pattern.sub(_sub, html, count=1)
        filled += 1
        print(f"  ✓ {name} : {size // 1024} Ko incrustés")
    open(HTML, "w", encoding="utf-8").write(html)
    print(f"{filled} image(s) incrustée(s) · guide : {len(html) // 1024} Ko")

if __name__ == "__main__":
    main()
