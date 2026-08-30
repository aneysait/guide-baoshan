#!/usr/bin/env python3
"""Remplit les emplacements photo du guide avec les fichiers de images/.

Chaque emplacement est un <div class="slot" data-img="nom.jpg">. Si images/nom.jpg
existe, il est redimensionné, recompressé, écrit dans assets/ et référencé par une
URL relative — pas de base64 : le lecteur ne télécharge que les images qu'il regarde.
Relancer après chaque nouvel ajout dans images/ ; c'est idempotent.
"""
import io, os, re, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None   # les photos de téléphone dépassent la limite anti-bombe

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "guide-baoshan.html")
IMGDIR = os.path.join(ROOT, "images")
ASSETS = os.path.join(ROOT, "assets")
MAX_W = 900           # largeur max : lisible à l'écran et correct à l'impression
JPEG_QUALITY = 76

def encode(path, portrait=False):
    im = Image.open(path)
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGB") if not path.lower().endswith(".png") else im.convert("RGBA")
    # les portraits n'ont pas besoin de 900 px de large : on allège nettement
    # les apercus de documents servent aussi de vue agrandie : on les garde plus fins
    target = 420 if portrait else (1300 if os.path.basename(path).startswith("apercu-") else MAX_W)
    if im.width > target:
        im = im.resize((target, round(im.height * target / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    base = os.path.basename(path).lower()
    # QR codes et logos gardent le PNG : la transparence doit survivre
    if "qr" in base or "logo" in base:
        im.save(buf, format="PNG", optimize=True)
        mime = "image/png"
    else:
        if im.mode in ("RGBA", "LA"):
            # sans ce fond blanc, PIL aplatit la transparence sur du NOIR
            fond = Image.new("RGB", im.size, (255, 255, 255))
            fond.paste(im, mask=im.split()[-1])
            im = fond
        im.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        mime = "image/jpeg"
    return mime, buf.getvalue(), im.size

def main():
    html = open(HTML, encoding="utf-8").read()
    slots = re.findall(r'<(?:div|span|label) class="slot([^"]*)" data-img="([^"]+)"([^>]*)>.*?</(?:div|span|label)>', html, re.S)
    if not slots:
        print("aucun emplacement libre — tout est déjà rempli ?")
    filled = 0
    for cls, name, extra in slots:
        path = os.path.join(IMGDIR, name)
        if not os.path.exists(path):
            print(f"  … {name} : en attente")
            continue
        mime, data, (w, h) = encode(path, "portrait" in cls)
        os.makedirs(ASSETS, exist_ok=True)
        asset = os.path.splitext(name)[0] + (".png" if mime.endswith("png") else ".jpg")
        open(os.path.join(ASSETS, asset), "wb").write(data)
        pattern = re.compile(r'<(div|span|label) class="slot' + re.escape(cls) + r'" data-img="' + re.escape(name) + r'"' + re.escape(extra) + r'>.*?</(?:div|span|label)>', re.S)
        def _sub(m):
            tag = m.group(1)
            # « filled » ne doit être ajouté qu'une fois, sinon la classe enfle à chaque passage
            klass = cls if " filled" in cls else cls + " filled"
            return (f'<{tag} class="slot{klass}" data-img="{name}"{extra}>'
                    f'<img src="assets/{asset}" loading="lazy" decoding="async" '
                    f'width="{w}" height="{h}" alt=""></{tag}>')
        html = pattern.sub(_sub, html, count=1)
        filled += 1
        print(f"  ✓ {name} → assets/{asset} : {len(data) // 1024} Ko")
    open(HTML, "w", encoding="utf-8").write(html)
    print(f"{filled} image(s) · guide : {len(html) // 1024} Ko · assets : "
          f"{sum(os.path.getsize(os.path.join(ASSETS, f)) for f in os.listdir(ASSETS)) // 1024} Ko")

if __name__ == "__main__":
    main()
