"""Crop georeferenced HOLC map scans (EPSG:3857 GeoTIFFs from Mapping Inequality) to an area extent and save as WebP.
Example:
  python analysis/build_scans.py VA_NewportNews_1937.tif data/newport-news-areas.json maps/newport-news/nn-1937.webp 2200
For Roanoke, the main sheet's printed Salem inset was masked out and the separate inset sheet composited at its real location.
"""
import json, math, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
R = 6378137
mx = lambda lon: R * math.radians(lon)
my = lambda lat: R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

def extent(geojson, pad=600):
    xs, ys = [], []
    def walk(c):
        if isinstance(c[0], (int, float)): xs.append(mx(c[0])); ys.append(my(c[1])); return
        for i in c: walk(i)
    for f in json.load(open(geojson))['features']: walk(f['geometry']['coordinates'])
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad

def warp(tif, X0, X1, Y0, Y1, W, H):
    im = Image.open(tif); t = im.tag_v2
    ox, oy = t[33922][3], t[33922][4]; px = t[33550][0]
    c0, c1, r0, r1 = (X0 - ox) / px, (X1 - ox) / px, (oy - Y1) / px, (oy - Y0) / px
    out = im.convert('RGBA').transform((W, H), Image.AFFINE, ((c1 - c0) / W, 0, c0, 0, (r1 - r0) / H, r0), resample=Image.BILINEAR, fillcolor=(0, 0, 0, 0))
    a = np.array(out); a[(a[:, :, 0] < 8) & (a[:, :, 1] < 8) & (a[:, :, 2] < 8), 3] = 0   # georeferencing corners -> transparent
    return Image.fromarray(a)

if __name__ == '__main__':
    tif, geo, dst, W = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    X0, X1, Y0, Y1 = extent(geo); H = round(W * (Y1 - Y0) / (X1 - X0))
    warp(tif, X0, X1, Y0, Y1, W, H).save(dst, quality=70, method=6)
    print(json.dumps({'x0': X0, 'x1': X1, 'y0': Y0, 'y1': Y1, 'w': W, 'h': H}))
