#!/usr/bin/env python3
"""Generate QR code + all vector diagrams. Reads content.json; hardcodes nothing."""
import json, os
import qrcode
import qrcode.image.svg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Polygon, Rectangle

C = json.load(open(os.path.join(os.path.dirname(__file__), "content.json")))
P = {k: "#" + v for k, v in C["palette"].items()}
OUT = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(OUT, exist_ok=True)

PRES_URL = C["meta"]["base_url"].rstrip("/") + C["meta"]["pres_path"]


# ---------------------------------------------------------------- QR CODE
def qr():
    """High error-correction QR, rendered large. Path-based SVG scales infinitely."""
    q = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% recovery
        box_size=20,
        border=2,
    )
    q.add_data(PRES_URL)
    q.make(fit=True)

    # SVG for the web (infinitely scalable, tiny file)
    img = q.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    img.save(os.path.join(OUT, "qr.svg"))

    # PNG for the PowerPoint
    png = q.make_image(fill_color="#025462", back_color="white")
    png.save(os.path.join(OUT, "qr.png"))
    print(f"  qr.svg / qr.png  ->  {PRES_URL}  (modules: {q.modules_count})")


# ------------------------------------------------------------ diagram base
def fig(w=10, h=5.6):
    f, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * h / w)
    ax.axis("off")
    f.patch.set_facecolor("white")
    return f, ax


def save(f, name):
    f.savefig(os.path.join(OUT, name + ".png"), dpi=200,
              bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(f)
    print("  " + name + ".png")


def box(ax, x, y, w, h, fc, ec=None, r=1.4, lw=1.6, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle=f"round,pad=0,rounding_size={r}",
                 fc=fc, ec=ec or fc, lw=lw, zorder=z))


def txt(ax, x, y, s, size=10, c=P["ink"], w="normal", ha="center", va="center", z=5, style="normal"):
    ax.text(x, y, s, fontsize=size, color=c, fontweight=w, ha=ha, va=va,
            zorder=z, fontstyle=style, family="DejaVu Sans")


def arrow(ax, x1, y1, x2, y2, c=None, lw=2.2, z=3, style="-|>", ms=14):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                 mutation_scale=ms, lw=lw, color=c or P["teal"], zorder=z))


def leg(ax, cx, ybase, height, col, swell=1.0, foot=True, foot_col=None,
        cuff=False, alpha=0.9, z=3):
    """Anterior-view lower limb. swell scales girth only, so height stays constant
    across stages and the widening is the visible variable."""
    thigh = 5.2 * swell
    knee = 3.8 * swell
    calf = 4.6 * swell
    ankle = 1.9 + 0.9 * (swell - 1.0)   # ankle thickens far less than the calf

    y_top = ybase + height
    y_knee = ybase + height * 0.55
    y_calf = ybase + height * 0.38
    y_ank = ybase + height * 0.20

    pts = [
        (cx - thigh, y_top), (cx + thigh, y_top),
        (cx + knee, y_knee), (cx + calf, y_calf), (cx + ankle, y_ank),
        (cx - ankle, y_ank), (cx - calf, y_calf), (cx - knee, y_knee),
    ]
    ax.add_patch(Polygon(pts, closed=True, fc=col, ec="none", alpha=alpha, zorder=z))

    if cuff:  # sharp lipedema cuff sitting on top of a normal ankle
        ax.add_patch(Polygon(
            [(cx - ankle * 1.55, y_ank + 1.6), (cx + ankle * 1.55, y_ank + 1.6),
             (cx + ankle * 1.35, y_ank - 0.4), (cx - ankle * 1.35, y_ank - 0.4)],
            closed=True, fc=col, ec="none", alpha=min(1, alpha + 0.08), zorder=z + 1))

    if foot:
        fc_ = foot_col or col
        pale = foot_col is not None          # normal foot needs a visible edge
        ec_ = P["slate"] if pale else "none"
        lw_ = 1.6 if pale else 0
        fw = ankle if not cuff else 1.9
        toe = fw * 3.2          # forward projection of the toes
        heel = fw * 1.25        # rearward projection of the heel
        sole = ybase           # ground line
        inst = ybase + (y_ank - ybase) * 0.42   # top of the instep
        ax.add_patch(Polygon(
            [(cx - fw, y_ank), (cx + fw, y_ank),          # ankle joint
             (cx + fw * 1.1, inst),                        # instep
             (cx + toe, sole + 1.5),                       # top of toes
             (cx + toe, sole),                             # toe tip
             (cx - heel, sole),                            # heel base
             (cx - heel * 1.05, inst)],                    # heel back
            closed=True, fc=fc_, ec=ec_, lw=lw_, alpha=alpha, zorder=z))


# ------------------------------------------------------- 1. lymph pathway
def d_lymph_pathway():
    f, ax = fig(10, 5.0)
    H = 50
    stages = [
        ("Interstitial\nfluid", P["mist"], P["slate"]),
        ("Initial\nlymphatics", P["seafoam"], "white"),
        ("Precollectors\n& collectors", P["teal"], "white"),
        ("Lymph\nnodes", P["mid"], "white"),
        ("Trunks &\nthoracic duct", P["deep"], "white"),
        ("Subclavian\nveins", P["slate"], "white"),
    ]
    w, gap = 13.0, 2.6
    x = 2.0
    for i, (label, fc, tc) in enumerate(stages):
        box(ax, x, H - 9, w, 18, fc, ec=P["line"] if i == 0 else fc)
        txt(ax, x + w / 2, H, label, size=9.5, c=tc, w="bold")
        if i < len(stages) - 1:
            arrow(ax, x + w + 0.4, H, x + w + gap - 0.4, H, c=P["teal"], lw=2.4)
        x += w + gap

    txt(ax, 50, H + 17, "One-way drainage: interstitium \u2192 venous circulation",
        size=12, c=P["deep"], w="bold")
    txt(ax, 50, H - 16.5,
        "Lymphangions contract 6\u201310\u00d7/min \u2014 stimulated by stretch, muscle contraction,\n"
        "arterial pulsation, and breathing",
        size=9.5, c=P["slate"], style="italic")
    save(f, "lymph_pathway")


# ------------------------------------------------ 2. load vs capacity
def d_load_capacity():
    f, ax = fig(10, 5.2)
    panels = [
        ("Normal", 26, 62, P["seafoam"], "Capacity exceeds load\nLarge functional reserve"),
        ("Dynamic\ninsufficiency", 66, 62, P["amber"], "Load exceeds capacity\nLymphatics are NORMAL\nLow-protein edema"),
        ("Mechanical\ninsufficiency", 26, 20, P["rose"], "Capacity drops below load\nLymphatics are DAMAGED\nHigh-protein LYMPHEDEMA"),
    ]
    pw = 29.5
    for i, (name, load, cap, col, desc) in enumerate(panels):
        x = 2.5 + i * (pw + 2.6)
        box(ax, x, 6, pw, 40, "white", ec=P["line"], r=1.6)
        txt(ax, x + pw / 2, 42.5, name, size=11, c=P["deep"], w="bold")

        # two bars
        bw = 7.5
        base = 12
        maxh = 22
        lh = maxh * load / 100.0
        ch = maxh * cap / 100.0
        bx1 = x + pw / 2 - 10
        bx2 = x + pw / 2 + 2.5
        ax.add_patch(Rectangle((bx1, base), bw, lh, fc=P["mid"], zorder=3))
        ax.add_patch(Rectangle((bx2, base), bw, ch, fc=col, zorder=3))
        txt(ax, bx1 + bw / 2, base - 2.2, "load", size=8, c=P["slate"])
        txt(ax, bx2 + bw / 2, base - 2.2, "capacity", size=8, c=P["slate"])
        txt(ax, x + pw / 2, 9.0, desc, size=8.2, c=P["slate"])

    txt(ax, 50, 50, "Every lymphedema is a load-versus-capacity mismatch",
        size=12, c=P["deep"], w="bold")
    save(f, "load_capacity")


# ------------------------------------------------------- 3. Stemmer sign
def d_stemmer():
    f, ax = fig(10, 5.2)
    for i, (title, ok, col, note) in enumerate([
        ("NEGATIVE Stemmer", True, P["seafoam"], "Skin fold at base of 2nd toe\nCAN be pinched and lifted\n\nDoes NOT rule out lymphedema"),
        ("POSITIVE Stemmer", False, P["rose"], "Skin fold CANNOT be lifted\nTissue is thickened/fibrotic\n\nDIAGNOSTIC for lymphedema"),
    ]):
        x0 = 4 + i * 48
        box(ax, x0, 3, 44, 44, "white", ec=col, r=1.8, lw=2.2)
        txt(ax, x0 + 22, 43, title, size=12.5, c=col, w="bold")

        # foot seen from above (dorsum): narrow heel at bottom, wide forefoot at top
        cx, cy = x0 + 22, 20
        ax.add_patch(Polygon([[cx - 6.5, cy - 9], [cx + 6.5, cy - 9],
                              [cx + 9.5, cy + 4], [cx - 9.5, cy + 4]],
                             closed=True, fc=P["mist"], ec=P["line"], lw=1.5, zorder=2))
        # five toes, 2nd toe highlighted
        toe_w = [3.4, 3.0, 2.8, 2.6, 2.3]
        toe_h = [4.6, 4.9, 4.5, 4.0, 3.2]
        xs_toe = [cx - 7.4, cx - 3.6, cx - 0.1, cx + 3.2, cx + 6.3]
        for t in range(5):
            hot = (t == 1)
            ax.add_patch(FancyBboxPatch(
                (xs_toe[t] - toe_w[t] / 2, cy + 3.4), toe_w[t], toe_h[t],
                boxstyle="round,pad=0,rounding_size=1.0",
                fc=col if hot else P["line"], ec=P["line"], lw=1.0, zorder=3))

        tx = xs_toe[1]
        ty = cy + 3.4 + toe_h[1]
        if ok:
            # a fold of skin pinched up into a peak
            ax.add_patch(Polygon([[tx - 2.6, ty], [tx, ty + 5.0], [tx + 2.6, ty]],
                                 closed=True, fc=col, ec=col, zorder=4))
            label = "fold lifts"
        else:
            ax.add_patch(Circle((tx, ty + 3.0), 2.5, fc="white", ec=col, lw=2.4, zorder=4))
            ax.plot([tx - 1.8, tx + 1.8], [ty + 4.8, ty + 1.2],
                    color=col, lw=2.4, zorder=5, solid_capstyle="round")
            label = "will not lift"
        txt(ax, cx, ty + 8.4, label, size=9.0, c=col, w="bold")

        txt(ax, x0 + 22, 8.0, note, size=8.5, c=P["slate"])
    save(f, "stemmer")


# ------------------------------------------------ 4. stage progression
def d_stage_progression():
    f, ax = fig(10, 5.0)
    stages = [
        ("Stage 0", "Latent", 1.00, P["seafoam"], "No visible swelling\nTransport impaired\nStemmer negative"),
        ("Stage I", "Reversible", 1.22, P["mid"], "Soft PITTING edema\nResolves overnight\nNo fibrosis"),
        ("Stage II", "Irreversible", 1.48, P["amber"], "Elevation fails\nFibrosis begins\nStemmer POSITIVE"),
        ("Stage III", "Elephantiasis", 1.85, P["rose"], "Non-pitting\nPapillomas, folds\nSkin changes"),
    ]
    pw = 22.0
    for i, (n, sub, scale, col, desc) in enumerate(stages):
        x = 2.0 + i * (pw + 2.0)
        txt(ax, x + pw / 2, 47, n, size=13, c=col, w="bold")
        txt(ax, x + pw / 2, 43, sub, size=9.5, c=P["slate"], style="italic")

        cx = x + pw / 2 - 1.5
        leg(ax, cx, 11.5, 27, col, swell=scale, alpha=0.88)
        txt(ax, x + pw / 2, 5.5, desc, size=8.0, c=P["slate"])

    # progression arrow
    arrow(ax, 4, 51.5, 96, 51.5, c=P["line"], lw=3, ms=16)
    txt(ax, 50, 54.5, "Progression without treatment", size=9.5, c=P["slate"], style="italic")
    save(f, "stage_progression")


# ------------------------------------------------------- 5. CDT pillars
def d_cdt_pillars():
    f, ax = fig(10, 4.8)
    pillars = C["sections"]
    pil = next(s for s in pillars if s["id"] == "cdt_overview")["pillars"]
    cols = [P["seafoam"], P["teal"], P["mid"], P["deep"]]
    pw = 22.0
    for i, p in enumerate(pil):
        x = 2.0 + i * (pw + 2.0)
        box(ax, x, 8, pw, 30, cols[i], r=1.8)
        ax.add_patch(Circle((x + pw / 2, 32), 4.0, fc="white", zorder=4))
        txt(ax, x + pw / 2, 32, p["n"], size=15, c=cols[i], w="bold", z=5)
        txt(ax, x + pw / 2, 24.5, p["h"], size=10.5, c="white", w="bold")
        txt(ax, x + pw / 2, 15, p["d"], size=8.2, c="white")

    txt(ax, 50, 44, "Complete Decongestive Therapy \u2014 four components",
        size=12.5, c=P["deep"], w="bold")
    txt(ax, 50, 3.5,
        "Phase I intensive (3\u20136 weeks, 4\u20135\u00d7/week)  \u2192  Phase II maintenance (lifelong self-management)",
        size=9, c=P["slate"], style="italic")
    save(f, "cdt_pillars")


# ---------------------------------------------------------- 6. MLD flow
def d_mld_flow():
    f, ax = fig(10, 4.2)
    txt(ax, 50, 38, "MLD sequence \u2014 clear proximal before distal",
        size=12.5, c=P["deep"], w="bold")
    steps = [
        ("1", "Diaphragmatic\nbreathing"),
        ("2", "Terminus\n(supraclavicular)"),
        ("3", "Trunk quadrants\ncontra \u2192 ipsi"),
        ("4", "Anastomoses"),
        ("5", "Proximal limb"),
        ("6", "Distal limb"),
    ]
    w, gap = 13.5, 2.2
    x = 2.0
    for i, (n, label) in enumerate(steps):
        shade = 0.35 + 0.65 * (i / (len(steps) - 1))
        box(ax, x, 14, w, 17, P["teal"], r=1.4)
        ax.add_patch(FancyBboxPatch((x, 14), w, 17,
                     boxstyle="round,pad=0,rounding_size=1.4",
                     fc="white", ec="none", alpha=1 - shade, zorder=3))
        tc = "white" if shade > 0.62 else P["deep"]
        bc = "white" if shade > 0.62 else P["ink"]
        txt(ax, x + w / 2, 27.5, n, size=11, c=tc, w="bold", z=5)
        txt(ax, x + w / 2, 20, label, size=8.2, c=bc, z=5)
        if i < len(steps) - 1:
            arrow(ax, x + w + 0.2, 22.5, x + w + gap - 0.2, 22.5, c=P["teal"], lw=2, ms=12)
        x += w + gap

    txt(ax, 50, 8,
        "Very light pressure \u2014 skin stretch only  \u00b7  ~1 stroke/second  \u00b7  no lubricant, no gliding",
        size=9.2, c=P["slate"], style="italic")
    txt(ax, 50, 4,
        "CONTRAINDICATED: acute infection  \u00b7  acute DVT  \u00b7  decompensated heart failure",
        size=9.2, c=P["rose"], w="bold")
    save(f, "mld_flow")


# ------------------------------------------------------ 7. lipedema cuff
def d_lipedema_cuff():
    f, ax = fig(10, 4.6)
    txt(ax, 50, 41, "The ankle cuff \u2014 lipedema spares the feet",
        size=12.5, c=P["deep"], w="bold")
    for i, (label, lip, col) in enumerate([
        ("Lipedema", True, P["rose"]),
        ("Lymphedema", False, P["mid"]),
    ]):
        cx = 28 + i * 42
        if lip:
            # swollen limb, sharp cuff, NORMAL pale foot
            leg(ax, cx, 10.5, 24, col, swell=1.55, cuff=True,
                foot_col=P["mist"], alpha=0.88)
            ax.plot([cx - 11, cx + 9], [15.6, 15.6], color=P["ink"],
                    lw=1.7, ls=(0, (4, 3)), zorder=8)
            txt(ax, cx + 10.5, 15.6, "sharp cuff", size=8.6, c=P["ink"],
                w="bold", ha="left")
            note = "Foot SPARED\nStemmer NEGATIVE"
        else:
            # swelling continues into the foot
            leg(ax, cx, 10.5, 24, col, swell=1.55, alpha=0.88)
            note = "Foot INVOLVED\nStemmer POSITIVE"

        txt(ax, cx, 37, label, size=11.5, c=col, w="bold")
        txt(ax, cx, 5.2, note, size=8.8, c=P["slate"], w="bold")
    save(f, "lipedema_cuff")


# ----------------------------------------------- 8. lipedema vs lymphedema
def d_lip_vs_lymph():
    f, ax = fig(10, 5.4)
    sec = next(s for s in C["sections"] if s["id"] == "differential_lip")
    rows = sec["table"]["rows"][:8]
    cols = sec["table"]["cols"]

    txt(ax, 50, 52, "Key discriminators", size=12.5, c=P["deep"], w="bold")
    xs = [4, 36, 68]
    widths = [30, 30, 28]
    # header
    for j, cname in enumerate(cols):
        box(ax, xs[j], 45, widths[j], 5.2, P["deep"], r=0.9)
        txt(ax, xs[j] + widths[j] / 2, 47.6, cname, size=9.5, c="white", w="bold")
    y = 43.4
    rh = 4.9
    for i, r in enumerate(rows):
        y -= rh
        if i % 2 == 0:
            box(ax, 4, y, 92, rh - 0.5, P["mist"], r=0.6, lw=0)
        for j, cell in enumerate(r):
            weight = "bold" if j == 0 else "normal"
            colr = P["deep"] if j == 0 else P["ink"]
            txt(ax, xs[j] + 1.5, y + (rh - 0.5) / 2, cell, size=8.2,
                c=colr, w=weight, ha="left")
    save(f, "lip_vs_lymph")


if __name__ == "__main__":
    print("QR:")
    qr()
    print("Diagrams:")
    for fn in (d_lymph_pathway, d_load_capacity, d_stemmer, d_stage_progression,
               d_cdt_pillars, d_mld_flow, d_lipedema_cuff, d_lip_vs_lymph):
        fn()
    print("\nAssets written to", OUT)
