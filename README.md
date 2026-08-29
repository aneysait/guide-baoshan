# Baoshan Handbook — UTSEUS

Handbook for exchange students spending a semester at UTSEUS
(Sino-European School of Technology), Shanghai University, Baoshan campus.

**Read it:**
- PC edition (A4 pages): https://aneysait.github.io/guide-baoshan/
- Phone edition: https://aneysait.github.io/guide-baoshan/phone.html

Written by Anicet Barrios, Head Student Coordinator, UTSEUS.
Base maps © OpenStreetMap contributors (ODbL).

## Rebuilding after a change

`guide-baoshan.html` is the single source. After editing it, run:

```sh
python3 embed_images.py   # fills any new photo slot from images/
python3 build.py          # regenerates index.html (PC) and phone.html
```
