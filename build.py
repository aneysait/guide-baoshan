#!/usr/bin/env python3
"""Builds the two published editions from the single source file.

    guide-baoshan.html   source (A4 page markup, images embedded)
      ├── index.html     PC edition — the A4 book, one page per sheet
      └── phone.html     phone edition — continuous scroll, big type, scrollable maps

Run after every content change:  python3 build.py
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "guide-baoshan.html")

SWITCH_CSS = """
  .switch{position:sticky;top:0;z-index:50;display:flex;justify-content:center;gap:4mm;
    background:var(--encre);color:#fff;font-family:var(--etroit);font-size:9pt;
    letter-spacing:.18em;text-transform:uppercase;padding:2.5mm 4mm;}
  .switch a{color:#fff;border-bottom:.3mm solid rgba(255,255,255,.5);}
  @media print{.switch{display:none;}}
"""

# Phone edition: overrides the A4 page metaphor entirely.
PHONE_CSS = """
  /* ---------- phone edition ---------- */
  html{scroll-padding-top:14mm;}
  body{background:var(--papier);font-size:16px;line-height:1.62;}
  .page{width:auto;min-height:0;margin:0;padding:26px 18px 30px;box-shadow:none;
    border-bottom:8px solid var(--panneau);overflow:visible;}
  .page.lisere::before{width:3mm;}
  .page.couverture{padding:0;border-bottom:0;}
  .couv-haut{padding:26px 18px 0;}
  .couv-centre{padding:34px 18px;}
  .couv-bas{padding:0 18px 26px;}
  .titre-couv{font-size:56pt;}
  .titre-couv small{font-size:18pt;}
  .titre-couv.duo{font-size:25pt;}
  .titre-couv.duo small{font-size:12pt;}
  .couv-sous{font-size:16px;max-width:none;}
  .vertical{display:none;}
  .pied{position:static;margin-top:22px;padding-top:10px;border-top:.3mm solid var(--filet);}
  /* Le numero de page reste utile en lecture continue : « regarde page 13 » doit
     vouloir dire quelque chose sur telephone aussi. */
  .pied .num{display:inline;}
  .pied .num::before{content:"page ";font-weight:400;letter-spacing:.18em;
    color:var(--encre-douce);}
  h1.chapitre{font-size:31px;}
  h2.bloc{font-size:15px;margin-top:26px;}
  .sur-titre{font-size:11px;}
  .chapo{font-size:17px;max-width:none;}
  .lieu .desc,.desc{font-size:15px;}
  .lieu .meta{font-size:13px;}
  .grille-2,.grille-3{grid-template-columns:1fr;gap:14px;}
  .lieu.resto{flex-direction:column;gap:12px;}
  .lieu.resto .slot{width:100%;}
  .slot,.slot.large,.lieu .slot,.lieu.resto .slot{min-height:0;max-height:none;
    width:100%!important;max-width:100%!important;}
  .lieu.pers .slot.portrait{width:26vw!important;max-width:26vw!important;flex:none;}
  .lieu.app .slot.logo{width:16mm!important;max-width:16mm!important;height:16mm;flex:none;}
  .evite .slot.logo{width:19mm!important;max-width:19mm!important;height:19mm;flex:none;}
  .esims .slot.logo{width:9mm!important;max-width:9mm!important;height:9mm;flex:none;}
  .slot img{height:auto;object-fit:contain;}
  /* Sur telephone la vignette occupe deja toute la largeur : agrandir ne sert que si
     l'image remplit la hauteur et se fait balayer lateralement. */
  .zoomer:checked + .doc-prev{width:auto!important;max-width:100vw!important;
    overflow:auto;-webkit-overflow-scrolling:touch;justify-content:flex-start;}
  .zoomer:checked + .doc-prev img{height:100%;width:auto;max-width:none;max-height:none;}
  .conseil,.panneau{font-size:15px;padding:14px 16px;}
  ul.liste li{margin-bottom:9px;}
  .sommaire li{font-size:19px;padding:12px 0;}
  .sommaire .sub{margin-left:0;font-size:12px;line-height:1.7;}
  .carte-legende{grid-template-columns:1fr;font-size:14px;gap:9px;}
  .grille-cartes{grid-template-columns:1fr 1fr;gap:18px 12px;}
  .vignette .slot.vig{height:22vw;min-height:0;}
  .vignette .slot.vig img{height:100%;object-fit:cover;}
  .slot.illus{height:auto;aspect-ratio:16/9;}
  .vignette .t{font-size:15px;}
  .vignette .d{font-size:13px;}
  .panneau.afec{flex-direction:column;align-items:flex-start;gap:14px;}
  .panneau.afec .afec-qr{align-self:center;}
  .slot.qr{width:34mm!important;height:34mm!important;max-width:none!important;}
  .legende{font-size:14px;}
  /* maps and diagrams keep their labels legible by scrolling sideways */
  .scroll-x{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -18px;padding:0 18px;}
  /* Les schemas vectoriels gardent le defilement lateral : leur texte est dans le SVG
     et retrecirait avec le dessin. */
  .scroll-x figure,.scroll-x svg{min-width:660px;}
  /* Les cartes matricielles tiennent dans l'ecran : pastilles et etiquettes sont du HTML
     dimensionne en mm, elles restent lisibles quelle que soit la taille du fond. */
  .scroll-x .carte-wrap{width:100%;min-width:0;}
  .carte-wrap .mlab{font-size:8px;padding:1px 3px;}
  .carte-wrap .pin{width:17px;height:17px;font-size:10px;}
  .carte-wrap .gate,.carte-wrap .lib{min-width:15px;height:15px;font-size:9px;}
  .carte-wrap .mdot{width:9px;height:9px;}
  .swipe{font-family:var(--etroit);font-size:12px;letter-spacing:.05em;
    color:var(--encre-douce);margin-top:5px;}
  .horaires{font-size:13px;}
  .credit,.carte-cap,figcaption{font-size:12px!important;}
"""


def renumber(h):
    """Footer numbers = physical sheet order. The cover is sheet 1 and carries none,
    so the first numbered page is 02. Recomputed on every build so it cannot drift."""
    seq = iter(range(2, 200))
    return re.sub(r'<span class="num">\d+</span>',
                  lambda m: '<span class="num">%02d</span>' % next(seq), h)


def read_source():
    h = open(SRC, encoding="utf-8").read()
    h2 = renumber(h)
    if h2 != h:
        open(SRC, "w", encoding="utf-8").write(h2)
        print("  page numbers renumbered")
        h = h2
    i = h.index("</style>")
    return h[:i], h[i + len("</style>"):]      # css block (without closing tag), body


def wrap_maps(body):
    """Phone only: let wide maps and diagrams scroll instead of shrinking to illegibility."""
    body = re.sub(r'(<div class="carte-wrap")', r'<div class="scroll-x">\1', body)
    # close the wrapper after the matching </div> that ends .carte-wrap
    out, depth, i = [], None, 0
    for m in re.finditer(r'<div class="scroll-x"><div class="carte-wrap"', body):
        pass
    # simpler: balance by scanning
    result, pos = [], 0
    for m in re.finditer(r'<div class="scroll-x"><div class="carte-wrap"', body):
        start = m.end()
        d = 1
        j = start
        while d and j < len(body):
            nxt_open = body.find("<div", j)
            nxt_close = body.find("</div>", j)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                d += 1
                j = nxt_open + 4
            else:
                d -= 1
                j = nxt_close + 6
        result.append((j, ))
    for (j, ) in reversed(result):
        body = body[:j] + "</div>" + body[j:]
    # the SVG figures (line 7 diagram, SIM/bank street map)
    body = re.sub(r'(<figure[^>]*>)(\s*<svg)', r'\1<div class="scroll-x">\2', body)
    body = re.sub(r'(</svg>)', r'\1</div>'
                  r'<div class="swipe">Swipe the diagram sideways to see the whole of it.</div>', body)
    return body


def page(lang_css, body, other, label, title_suffix=""):
    switch = (f'<div class="switch"><span>{label}</span>'
              f'<a href="{other[0]}">{other[1]}</a></div>\n')
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            + (lang_css.replace("<title>Baoshan Handbook</title>",
                                f"<title>Baoshan Handbook{title_suffix}</title>")
               if title_suffix else lang_css)
            + "</style>\n</head>\n<body>\n" + switch + body + "\n</body>\n</html>\n")


def main():
    css, body = read_source()

    desktop = page(css + SWITCH_CSS, body,
                   ("phone.html", "Open the phone edition →"), "PC edition")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(desktop)

    phone_body = wrap_maps(body)
    phone = page(css + SWITCH_CSS + PHONE_CSS, phone_body,
                 ("index.html", "Open the PC edition →"), "Phone edition", " · Phone")
    open(os.path.join(ROOT, "phone.html"), "w", encoding="utf-8").write(phone)

    for f in ("index.html", "phone.html"):
        p = os.path.join(ROOT, f)
        print(f"  {f}: {os.path.getsize(p)//1024} Ko")


if __name__ == "__main__":
    main()
