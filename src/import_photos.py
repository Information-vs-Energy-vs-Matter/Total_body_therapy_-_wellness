#!/usr/bin/env python3
"""Map /mnt/project images -> named slots in assets/photos/.

Several images are phone screenshots of an image viewer, so they carry close
buttons, next/prev arrows and filename captions. `crop` removes that chrome as a
fraction of each edge: (left, top, right, bottom).
"""
import os, json
from PIL import Image

SRC = "/mnt/project"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "photos")
os.makedirs(OUT, exist_ok=True)

# slot, source, crop(l,t,r,b) as fractions, note
MAP = [
    # ---------- anatomy (Cancer Research UK style diagrams) ----------
    ("anat_lymphatic_system",  "IMG_6928.jpg", (.05, .145, .05, .02), "whole-body lymphatic system"),
    ("anat_lymph_capillary",   "IMG_6929.jpg", (.02, .105, .02, .02), "lymphatic capillary + interstitium"),
    ("anat_node_regions",      "IMG_6930.jpg", (.03, .125, .03, .22), "pelvic lymph nodes"),
    ("anat_axillary_nodes",    "IMG_6931.jpg", (.03, .125, .03, .02), "breast / axillary nodes"),

    # ---------- lymphedema staging & presentation ----------
    ("stage_progression_photo", "IMG_7267.jpg", (0, .02, 0, .04), "legs, stages 1-4"),
    ("stage_upper_limb",        "IMG_6935.jpg", (0, .225, 0, .25), "upper limb, stages 1-4"),
    ("stage_clinical_leg",      "IMG_7266.jpg", (0, .02, 0, .01), "unilateral leg lymphedema"),
    ("stage1_photo",            "IMG_6937.jpg", (0, .095, .09, .15), "unilateral leg, earlier stage"),
    ("stage3_photo",            "IMG_6936.jpg", (0, .145, 0, .21), "stage 3, legs"),
    ("stage3_skin",             "IMG_6933.jpg", (0, .03, .08, .01), "stage 3 skin changes, lymphorrhea"),
    ("dx_imaging",              "IMG_6938.jpg", (0, .195, 0, .01), "limb + lymphoscintigraphy"),

    # ---------- Sara's own clinical photos ----------
    ("tbtw_skin_changes",   "patient_5_b.jpg", None, "ankle, crusting / weeping"),
    ("tbtw_bandaged_leg",   "patient_5_d.jpg", None, "bilateral, one bandaged"),
    ("tbtw_lymphorrhea",    "patient_5c.jpg",  None, "lower leg, crusting"),
    ("tbtw_arm_trunk",      "patient_4a.jpg",  None, "upper limb + trunk, anterior"),
    ("tbtw_arm_posterior",  "patient_4b.jpg",  None, "upper limb + trunk, posterior"),
    ("tbtw_arm_extended",   "patient_4d.jpg",  None, "arm extended"),
    ("tbtw_arm_raised",     "patient_4e.jpg",  None, "arm raised"),
    ("tbtw_severe_foot",    "patient_1c.jpg",  None, "severe foot / ankle involvement"),
    ("tbtw_cellulitis",     "patient_1a.jpg",  None, "bilateral, erythema"),

    # ---------- lipedema ----------
    ("lip_clinical_legs",   "IMG_7263.jpg", (0, .02, 0, .01), "lipedema legs, cuff visible"),
    ("lip_stage3",          "IMG_7265.jpg", (0, .01, 0, .01), "advanced lipedema, mottling"),
    ("lip_foot_sparing",    "IMG_7264.jpg", (0, .01, 0, .01), "foot involvement vs sparing"),
    ("lip_body_1",          "IMG_7269.jpg", None, "lipedema body habitus"),
    ("lip_body_2",          "IMG_7271.jpg", None, "lipedema body habitus"),
    ("lip_body_3",          "IMG_7270.jpg", None, "lipedema body habitus"),
    ("lip_before_front",    "Before_diagnosis1.jpg", None, "before diagnosis, anterior"),
    ("lip_before_side",     "Before_diagnosis2.jpg", None, "before diagnosis, lateral"),
    ("lip_surgical_markup", "2ndsurgery1.jpg", None, "pre-op markings"),
    ("lip_comparison_1",    "comparison.jpeg",  None, "before / after"),
    ("lip_comparison_2",    "comparison2.jpeg", None, "before / after, anterior"),
    ("lip_comparison_3",    "comparison3.jpeg", None, "before / after, posterior"),
# ---------- compression garments (manufacturer product images) ----------
    ("garment_thigh_high",  "IMG_7281.jpg", (.03, .02, .03, .02), "thigh-high, silicone band"),
    ("garment_pantyhose",   "IMG_7282.jpg", (.05, .06, .05, .03), "pantyhose / waist-high"),
    ("garment_wrap_arm",    "IMG_7283.jpg", (.02, .03, .02, .02), "Velcro wrap, upper limb"),
    ("garment_wrap_calf",   "IMG_7284.jpg", (.04, .04, .04, .04), "Velcro wrap, calf"),
    ("garment_wrap_foot",   "IMG_7285.jpg", (.03, .03, .03, .03), "Velcro wrap, foot / ankle"),
    ("garment_bra",         "IMG_7286.jpg", (.13, .03, .13, .03), "compression bra / trunk garment"),
]

# excluded on purpose
EXCLUDE = {
    "IMG_7268.jpg": "VISIBLE COPYRIGHT WATERMARK - (c) Lipedema Simplified LLC. Do not publish.",
    "IMG_6932.jpg": "Screenshot of a web search results page, not a usable figure.",
    "IMG_6944.jpg": "Duplicate of IMG_6935.jpg.",
}

MAXW = 1600


def main():
    report = []
    for slot, src, crop, note in MAP:
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            report.append((slot, src, "MISSING", ""))
            continue
        im = Image.open(p).convert("RGB")
        w, h = im.size
        if crop:
            l, t, r, b = crop
            im = im.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b))))
        if im.width > MAXW:
            im = im.resize((MAXW, int(im.height * MAXW / im.width)), Image.LANCZOS)
        out = os.path.join(OUT, slot + ".jpg")
        im.save(out, quality=90, optimize=True)
        report.append((slot, src, "%dx%d" % im.size, note))

    print("%-24s %-22s %-11s %s" % ("SLOT", "SOURCE", "SIZE", "NOTE"))
    for r in report:
        print("%-24s %-22s %-11s %s" % r)
    print("\nwrote %d images to %s" % (len(report), OUT))
    print("\nEXCLUDED:")
    for k, v in EXCLUDE.items():
        print("  %-18s %s" % (k, v))


if __name__ == "__main__":
    main()
