#!/usr/bin/env python3
"""
Generates app.ico — a multi-size ICO (16/24/32/48/64/128/256 px)
Theme: magnifying glass over a git branch node (circles + lines)
"""
from PIL import Image, ImageDraw
import math

def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size

    # ── Palette ──────────────────────────────────────────────
    BG        = (10,  10,  10, 255)   # pure black
    BRANCH_C  = (0,   230,  80, 255)  # bright green main node
    BRANCH_S  = (0,   200,  60, 255)  # mid green sub node
    BRANCH_L  = (0,   255, 120, 255)  # vivid green leaf node
    LINE_COL  = (0,   180,  50, 255)  # green lines
    GLASS_RIM = (0,   255,  80, 255)  # bright green rim
    GLASS_LEN = (0,   255,  80, 255)  # bright green handle
    GLASS_BG  = (0,   255,  80,  30)  # faint green glass fill

    # ── Background rounded rect ───────────────────────────────
    r = max(3, s // 8)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r, fill=BG)

    # ── Git branch diagram (left 55% of icon) ────────────────
    lw = max(1, s // 20)

    # Node radii
    nr_big  = max(2, s // 10)
    nr_sml  = max(1, s //  14)

    # Node centres (all in icon space)
    cx_root = round(s * 0.20)
    cy_root = round(s * 0.25)

    cx_mid  = round(s * 0.20)
    cy_mid  = round(s * 0.55)

    cx_leaf = round(s * 0.20)
    cy_leaf = round(s * 0.82)

    cx_side = round(s * 0.42)
    cy_side = round(s * 0.55)

    # Lines first (under nodes)
    d.line([(cx_root, cy_root + nr_big), (cx_mid, cy_mid - nr_sml)], fill=LINE_COL, width=lw)
    d.line([(cx_mid,  cy_mid  + nr_sml), (cx_leaf, cy_leaf - nr_sml)], fill=LINE_COL, width=lw)
    d.line([(cx_mid,  cy_mid),  (cx_side, cy_side)], fill=LINE_COL, width=lw)

    # Nodes
    def circle(cx, cy, nr, col):
        d.ellipse([cx - nr, cy - nr, cx + nr, cy + nr], fill=col)

    circle(cx_root, cy_root, nr_big, BRANCH_C)
    circle(cx_mid,  cy_mid,  nr_sml, BRANCH_C)
    circle(cx_leaf, cy_leaf, nr_sml, BRANCH_S)
    circle(cx_side, cy_side, nr_sml, BRANCH_L)

    # ── Magnifying glass (right-bottom quadrant) ──────────────
    gx = round(s * 0.68)
    gy = round(s * 0.32)
    gr = round(s * 0.22)           # glass outer radius
    rim_w = max(1, s // 18)

    # semi-transparent fill
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=GLASS_BG)
    # rim
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr],
              outline=GLASS_RIM, width=rim_w)

    # handle — towards bottom-right at 45°
    hlen = round(s * 0.20)
    hx1  = round(gx + gr * math.cos(math.radians(45)))
    hy1  = round(gy + gr * math.sin(math.radians(45)))
    hx2  = round(hx1 + hlen * math.cos(math.radians(45)))
    hy2  = round(hy1 + hlen * math.sin(math.radians(45)))
    hw   = max(1, s // 14)
    # rounded cap: draw a thick line then circles on each end
    d.line([(hx1, hy1), (hx2, hy2)], fill=GLASS_LEN, width=hw)
    cap = hw // 2
    d.ellipse([hx1 - cap, hy1 - cap, hx1 + cap, hy1 + cap], fill=GLASS_LEN)
    d.ellipse([hx2 - cap, hy2 - cap, hx2 + cap, hy2 + cap], fill=GLASS_LEN)

    return img


def main():
    sizes   = [256, 128, 64, 48, 32, 24, 16]
    images  = [draw_icon(s) for s in sizes]
    out     = "app.ico"
    # PIL saves multi-size ICO when given a list via append_images
    images[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"✅  {out} created with sizes: {sizes}")


if __name__ == "__main__":
    main()
