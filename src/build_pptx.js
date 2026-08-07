// content.json -> .pptx   (no reader-visible string is hardcoded here)
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const HERE = __dirname;
const C = JSON.parse(fs.readFileSync(path.join(HERE, "content.json"), "utf8"));
const M = C.meta, P = C.palette;
const A = (n) => path.join(HERE, "assets", n + ".png");

// captured photos land in assets/photos/ — use them when present
const PHOTO_DIR = path.join(HERE, "assets", "photos");
const PHOTO_EXT = [".png", ".jpg", ".jpeg", ".webp"];
function photo(name) {
  for (const e of PHOTO_EXT) {
    const f = path.join(PHOTO_DIR, name + e);
    if (fs.existsSync(f)) return f;
  }
  return null;
}
/** first available captured photo for a section, else null */
function secPhoto(sec) {
  for (const nm of (sec.photos || [])) { const f = photo(nm); if (f) return f; }
  return null;
}
let PHOTOS_USED = 0;
const S = (id) => C.sections.find((s) => s.id === id);

const W = 13.333, H = 7.5;
const MX = 0.62;                       // side margin
const CW = W - MX * 2;                 // content width

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // MUST precede addSlide
pres.author = M.presenter;
// pptxgenjs escapes dc:title/dc:creator but writes <Company> into docProps/app.xml
// raw, so a literal "&" produces invalid XML. Pre-escape this field only.
pres.company = M.org.replace(/&/g, "&amp;");
pres.title = M.title;

let n = 0;
const CUT = [];

// strip **bold** markers for PowerPoint plain runs
const clean = (s) => s.replace(/\*\*/g, "");
// pptxgenjs array form is {text, options}. Properties as siblings of `text` are
// silently dropped — which is why breakLine must live inside options.
function richRun(s, opt) {
  const m = s.match(/^\*\*(.+?)\*\*(.*)$/);
  if (!m) return [{ text: s.replace(/\*\*/g, ""), options: Object.assign({}, opt) }];
  // Only the FIRST run of a paragraph may carry `bullet`; if the continuation run
  // carries it too, pptxgenjs emits a second bulleted paragraph.
  const tail = Object.assign({}, opt);
  delete tail.bullet;
  return [
    { text: m[1], options: Object.assign({}, opt, { bold: true, breakLine: false }) },
    { text: m[2].replace(/\*\*/g, ""), options: tail },
  ];
}

// ---- text metrics: estimate wrapped line count so cards can be auto-fitted ----
function estLines(t, size, wIn) {
  const cpl = Math.max(8, Math.floor((wIn * 96) / (size * 0.47)));
  return Math.max(1, Math.ceil(t.length / cpl));
}

function blockH(b, size, wIn) {
  const lh = (size * 1.34) / 72;              // inches per rendered line
  let h = 0.30 + 0.16;                        // header height + gap below it
  b.items.forEach((it) => {
    h += estLines(clean(it), size, wIn - 0.30) * lh + 0.06;
  });
  return h + 0.28;                            // bottom padding
}

/** largest size in `sizes` where every block fits its allotted height */
function fitSize(blocks, wIn, hAvail, sizes) {
  for (const s of (sizes || [13, 12.5, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5])) {
    if (blocks.every((b) => blockH(b, s, wIn) <= hAvail)) return s;
  }
  return 8;
}

/** largest size where the SUM of stacked block heights fits */
function fitStack(blocks, wIn, hTotal, gap, sizes) {
  for (const s of (sizes || [13, 12.5, 12, 11.5, 11, 10.5, 10, 9.5, 9, 8.5])) {
    const tot = blocks.reduce((a, b) => a + blockH(b, s, wIn), 0)
      + gap * (blocks.length - 1);
    if (tot <= hTotal) return s;
  }
  return 8;
}

function notes(slide, s, extra) {
  const bits = [];
  if (s && s.cuttable) { bits.push("[OPTIONAL — safe to cut]"); CUT.push(n + ". " + s.title); }
  if (s && s.note) bits.push(clean(s.note));
  if (extra) bits.push(extra);
  if (bits.length) slide.addNotes(bits.join("\n\n"));
}

// ---------------------------------------------------------------- chrome
function head(slide, kicker, title, dark) {
  if (kicker) {
    slide.addText(kicker.toUpperCase(), {
      x: MX, y: 0.34, w: CW, h: 0.3, fontSize: 11, bold: true,
      color: dark ? "8FD3DE" : P.teal, charSpacing: 2,
      fontFace: "Calibri", margin: 0,
    });
  }
  slide.addText(title, {
    x: MX, y: kicker ? 0.66 : 0.5, w: CW, h: 0.85,
    fontSize: 34, bold: true, color: dark ? "FFFFFF" : P.deep,
    fontFace: "Cambria", margin: 0, valign: "top",
  });
}

function lead(slide, text, y) {
  if (!text) return y;
  slide.addText(clean(text), {
    x: MX, y: y, w: CW, h: 0.62, fontSize: 15, color: P.slate,
    fontFace: "Calibri", margin: 0, valign: "top",
  });
  return y + 0.72;
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: fill || "FFFFFF" },
    line: { color: P.line, width: 1 }, rectRadius: 0.09,
  });
}

function bullets(slide, items, x, y, w, h, size) {
  const runs = [];
  items.forEach((it, i) => {
    richRun(it, {
      fontSize: size || 13, color: P.ink, fontFace: "Calibri",
      bullet: { code: "2022", indent: 15 },
      paraSpaceAfter: 6, breakLine: i < items.length - 1,
    }).forEach((r) => runs.push(r));
  });
  slide.addText(runs, { x, y, w, h, margin: 0, valign: "top" });
}

function newSlide(dark) {
  n += 1;
  const s = pres.addSlide();
  s.background = { color: dark ? P.deep : P.mist };
  if (!dark) {
    s.addText(String(n), {
      x: W - 0.85, y: H - 0.52, w: 0.5, h: 0.3, fontSize: 10,
      color: "9BB0B8", align: "right", fontFace: "Calibri", margin: 0,
    });
  }
  return s;
}

// ============================================================ 1  TITLE
(function () {
  const s = newSlide(true);
  s.addText(M.org.toUpperCase(), {
    x: MX, y: 1.35, w: CW, h: 0.32, fontSize: 13, bold: true,
    color: "8FD3DE", charSpacing: 2.5, fontFace: "Calibri", margin: 0,
  });
  s.addText(M.title, {
    x: MX, y: 1.85, w: 8.6, h: 1.5, fontSize: 50, bold: true,
    color: "FFFFFF", fontFace: "Cambria", margin: 0, valign: "top",
  });
  s.addText(M.subtitle, {
    x: MX, y: 3.35, w: 8.4, h: 0.85, fontSize: 19, color: "CBE6EB",
    fontFace: "Calibri", margin: 0, valign: "top",
  });
  s.addShape(pres.ShapeType.line, {
    x: MX, y: 4.55, w: 6.2, h: 0, line: { color: "3E7C8A", width: 1 },
  });
  s.addText(
    [{ text: M.presenter, options: { bold: true, fontSize: 19, color: "FFFFFF", breakLine: true } },
     { text: M.presenter_creds, options: { fontSize: 13, color: "A8CFD8", breakLine: true } },
     { text: M.presenter_role, options: { fontSize: 13, color: "CBE6EB" } }],
    { x: MX, y: 4.8, w: 8.4, h: 1.3, fontFace: "Calibri", margin: 0, valign: "top" }
  );
  // QR panel
  s.addShape(pres.ShapeType.roundRect, {
    x: 9.7, y: 1.8, w: 3.05, h: 3.75, fill: { color: "FFFFFF" },
    line: { color: "FFFFFF", width: 0 }, rectRadius: 0.12,
  });
  s.addImage({ path: A("qr"), x: 10.05, y: 2.4, w: 2.35, h: 2.35 });
  s.addText("SCAN TO FOLLOW ALONG", {
    x: 9.7, y: 2.0, w: 3.05, h: 0.3, fontSize: 10, bold: true,
    color: P.deep, align: "center", charSpacing: 1.2, fontFace: "Calibri", margin: 0,
  });
  s.addText("Presentation, outline & self-check quiz", {
    x: 9.75, y: 4.85, w: 2.95, h: 0.5, fontSize: 9.5, color: P.slate,
    align: "center", fontFace: "Calibri", margin: 0,
  });
  s.addText(M.address + "  ·  " + M.phone + "  ·  " + M.website, {
    x: MX, y: H - 0.72, w: CW, h: 0.3, fontSize: 11, color: "8FB4BE",
    fontFace: "Calibri", margin: 0,
  });
  s.addNotes("Welcome. Point the room at the QR code before you start — it opens this "
    + "presentation, the outline, and a 12-question self-check quiz.\n\n"
    + M.disclaimer);
})();

// ============================================================ 2  ABOUT
(function () {
  const ab = C.about_org;
  const s = newSlide();
  head(s, "About", ab.heading);
  let y = lead(s, ab.body, 1.72);
  card(s, MX, y, CW, 2.9);
  bullets(s, ab.points, MX + 0.35, y + 0.3, CW - 0.7, 2.4, 15);
  s.addText(M.address + "  ·  " + M.phone + "  ·  " + M.website, {
    x: MX, y: y + 3.15, w: CW, h: 0.3, fontSize: 12, color: P.slate,
    fontFace: "Calibri", margin: 0,
  });
  s.addNotes("Establish credibility briefly, then move on. Both therapists are CLTs.");
})();

// ============================================================ 3  OBJECTIVES
(function () {
  const s = newSlide();
  head(s, "Objectives", "On completion you will be able to");
  const half = Math.ceil(C.objectives.length / 2);
  [[0, half, MX], [half, C.objectives.length, MX + CW / 2 + 0.15]].forEach(([a, b, x]) => {
    const runs = [];
    C.objectives.slice(a, b).forEach((o, i, arr) => {
      runs.push({
        text: String(a + i + 1) + ".  ",
        options: { bold: true, fontSize: 13, color: P.teal, fontFace: "Calibri" },
      });
      runs.push({
        text: o,
        options: {
          fontSize: 13, color: P.ink, fontFace: "Calibri",
          paraSpaceAfter: 10, breakLine: i < arr.length - 1,
        },
      });
    });
    s.addText(runs, { x, y: 1.85, w: CW / 2 - 0.15, h: 4.6, margin: 0, valign: "top" });
  });
  s.addNotes("Read these quickly — they double as the roadmap for the session.");
})();

// ==================================================== generic content slide
function contentSlide(id, opt) {
  opt = opt || {};
  const sec = S(id);
  const s = newSlide();
  head(s, opt.kicker || sec.kicker, opt.title || sec.title);
  let y = lead(s, opt.noLead ? null : sec.lead, 1.72);

  const blocks = opt.blocks
    ? opt.blocks.map((i) => sec.blocks[i])
    : (sec.blocks || []);
  let img = opt.image !== undefined ? opt.image : sec.diagram;
  let imgPath = img ? A(img) : null;
  const cap = opt.image === undefined ? secPhoto(sec) : null;
  if (cap) { imgPath = cap; img = true; PHOTOS_USED += 1; }
  const BOT = 0.62;                       // bottom margin
  const avail = H - y - BOT;

  if (img && !blocks.length) {
    s.addImage({
      path: imgPath, x: MX, y: y, w: CW, h: avail,
      sizing: { type: "contain", w: CW, h: avail },
    });
  } else if (img) {
    // image right, stacked cards left — size cards to their measured content
    const iw = 5.35;
    const bw = CW - iw - 0.45;
    const gap = 0.18;
    const size = fitStack(blocks, bw - 0.56, avail, gap);
    s.addImage({
      path: imgPath, x: W - MX - iw, y: y + 0.1, w: iw, h: Math.min(3.6, avail - 0.2),
      sizing: { type: "contain", w: iw, h: Math.min(3.6, avail - 0.2) },
    });
    let by = y;
    blocks.forEach((b) => {
      const h = blockH(b, size, bw - 0.56);
      card(s, MX, by, bw, h);
      s.addText(b.h, {
        x: MX + 0.28, y: by + 0.14, w: bw - 0.56, h: 0.3, fontSize: size + 1.5,
        bold: true, color: P.deep, fontFace: "Calibri", margin: 0,
      });
      bullets(s, b.items, MX + 0.28, by + 0.52, bw - 0.56, h - 0.7, size);
      by += h + gap;
    });
  } else {
    const cols = blocks.length >= 3 ? 3 : (blocks.length || 1);
    const rows = Math.ceil(blocks.length / cols);
    const gap = 0.22;
    const cw = (CW - gap * (cols - 1)) / cols;
    const rh = (avail - gap * (rows - 1)) / rows;
    const size = fitSize(blocks, cw - 0.48, rh, [13.5, 13, 12.5, 12, 11.5, 11, 10.5, 10, 9.5, 9]);
    blocks.forEach((b, i) => {
      const x = MX + (i % cols) * (cw + gap);
      const cy = y + Math.floor(i / cols) * (rh + gap);
      // card hugs its content, but never exceeds the row height
      const h = Math.min(rh, Math.max(1.1, blockH(b, size, cw - 0.48)));
      card(s, x, cy, cw, h);
      s.addText(b.h, {
        x: x + 0.24, y: cy + 0.14, w: cw - 0.48, h: 0.32, fontSize: size + 1.5,
        bold: true, color: P.deep, fontFace: "Calibri", margin: 0,
      });
      bullets(s, b.items, x + 0.24, cy + 0.54, cw - 0.48, h - 0.72, size);
    });
  }
  notes(s, sec, opt.notes);
  return s;
}

// ==================================================== full-bleed diagram
function diagramSlide(id, opt) {
  opt = opt || {};
  const sec = S(id);
  const s = newSlide();
  head(s, sec.kicker, opt.title || sec.title);
  let y = lead(s, sec.lead, 1.72);
  const ih = H - y - 1.0;
  s.addImage({
    path: A(opt.image || sec.diagram), x: MX, y: y, w: CW, h: ih,
    sizing: { type: "contain", w: CW, h: ih },
  });
  if (sec.note) {
    s.addText(clean(sec.note), {
      x: MX, y: H - 0.92, w: CW, h: 0.55, fontSize: 11, italic: true,
      color: P.slate, fontFace: "Calibri", margin: 0, valign: "top",
    });
  }
  notes(s, sec, opt.notes);
  return s;
}

// ==================================================== table slide
function tableSlide(id, opt) {
  opt = opt || {};
  const sec = S(id);
  const s = newSlide();
  head(s, sec.kicker, sec.title);
  let y = lead(s, sec.lead, 1.72);

  const t = sec.table;
  const rows = [t.cols.map((c) => ({
    text: c,
    options: { bold: true, color: "FFFFFF", fill: { color: P.deep }, fontSize: 12 },
  }))];
  t.rows.forEach((r, i) => {
    rows.push(r.map((cell, j) => ({
      text: clean(cell),
      options: {
        fontSize: opt.size || 11,
        bold: j === 0,
        color: j === 0 ? P.deep : P.ink,
        fill: { color: i % 2 ? "FFFFFF" : P.mist },
      },
    })));
  });
  s.addTable(rows, {
    x: MX, y: y, w: CW, colW: opt.colW,
    border: { type: "solid", color: P.line, pt: 1 },
    fontFace: "Calibri", valign: "middle", autoPage: false,
    rowH: opt.rowH || 0.34,
  });
  if (sec.note) {
    s.addText(clean(sec.note), {
      x: MX, y: H - 0.85, w: CW, h: 0.5, fontSize: 10.5, italic: true,
      color: P.slate, fontFace: "Calibri", margin: 0, valign: "top",
    });
  }
  notes(s, sec, opt.notes);
  return s;
}

// ==================================================== stage detail slide
function stageSlide(id) {
  const sec = S(id);
  const s = newSlide();
  s.addShape(pres.ShapeType.roundRect, {
    x: MX, y: 0.34, w: 1.5, h: 0.42, fill: { color: P.deep },
    line: { color: P.deep, width: 0 }, rectRadius: 0.2,
  });
  s.addText(sec.stage_label.toUpperCase(), {
    x: MX, y: 0.34, w: 1.5, h: 0.42, fontSize: 12, bold: true, color: "FFFFFF",
    align: "center", valign: "middle", fontFace: "Calibri", margin: 0,
  });
  s.addText(sec.title, {
    x: MX + 1.7, y: 0.3, w: CW - 1.7, h: 0.5, fontSize: 30, bold: true,
    color: P.deep, fontFace: "Cambria", margin: 0, valign: "middle",
  });
  let y = lead(s, sec.lead, 1.0);

  const cols = sec.blocks.length;
  const gap = 0.25;
  const cw = (CW - gap * (cols - 1)) / cols;
  const noteH = sec.note ? 0.62 : 0;
  const ch = H - y - 0.62 - noteH;
  const size = fitSize(sec.blocks, cw - 0.52, ch, [13, 12.5, 12, 11.5, 11, 10.5, 10, 9.5]);
  sec.blocks.forEach((b, i) => {
    const x = MX + i * (cw + gap);
    const h = Math.min(ch, Math.max(1.2, blockH(b, size, cw - 0.52)));
    card(s, x, y, cw, h);
    s.addText(b.h, {
      x: x + 0.26, y: y + 0.16, w: cw - 0.52, h: 0.32, fontSize: size + 1.5, bold: true,
      color: P.deep, fontFace: "Calibri", margin: 0,
    });
    bullets(s, b.items, x + 0.26, y + 0.58, cw - 0.52, h - 0.76, size);
  });
  if (sec.note) {
    s.addText(clean(sec.note), {
      x: MX, y: y + ch + 0.14, w: CW, h: 0.5, fontSize: 11, italic: true,
      color: P.slate, fontFace: "Calibri", margin: 0, valign: "top",
    });
  }
  const sp = secPhoto(sec);
  if (sp) {
    PHOTOS_USED += 1;
    s.addImage({ path: sp, x: W - MX - 3.2, y: 0.95, w: 3.2, h: 2.4,
                 sizing: { type: "contain", w: 3.2, h: 2.4 } });
  }
  notes(s, sec, "Photo slot: " + (sec.photo_slot || "n/a"));
  return s;
}

// ======================================================== BUILD ORDER
diagramSlide("anatomy");
contentSlide("anatomy", { title: "Lymphatic System — Pathway & Function", image: null, kicker: "Foundations" });
diagramSlide("load_capacity");
contentSlide("etiology");
contentSlide("symptoms");
contentSlide("diagnosis", { blocks: [0, 1], image: "stemmer", title: "Diagnosis — History & Examination" });
contentSlide("diagnosis", { blocks: [2, 3], image: null, noLead: true, title: "Diagnosis — Measurement & Imaging" });
tableSlide("differential_general", { colW: [3.0, 9.11], size: 11, rowH: 0.42 });
diagramSlide("staging_overview");
stageSlide("stage_0");
stageSlide("stage_1");
stageSlide("stage_2");
stageSlide("stage_3");
diagramSlide("cdt_overview", { title: "Complete Decongestive Therapy" });

// CDT phases (blocks only)
(function () {
  const sec = S("cdt_overview");
  const s = newSlide();
  head(s, "Treatment", "CDT — Two Phases");
  let y = 1.72;
  const cw = (CW - 0.3) / 2;
  sec.blocks.forEach((b, i) => {
    const x = MX + i * (cw + 0.3);
    card(s, x, y, cw, 3.6);
    s.addText(b.h, {
      x: x + 0.3, y: y + 0.22, w: cw - 0.6, h: 0.4, fontSize: 16, bold: true,
      color: P.deep, fontFace: "Calibri", margin: 0,
    });
    bullets(s, b.items, x + 0.3, y + 0.75, cw - 0.6, 2.7, 13);
  });
  s.addText(clean(sec.note), {
    x: MX, y: y + 3.8, w: CW, h: 0.5, fontSize: 12, italic: true,
    color: P.slate, fontFace: "Calibri", margin: 0, valign: "top",
  });
  s.addNotes(clean(sec.note));
})();

contentSlide("skin_care");
contentSlide("mld", { blocks: [0, 1], image: null, title: "Manual Lymphatic Drainage — Technique" });
diagramSlide("mld", { title: "MLD — Sequence & Contraindications", image: "mld_flow" });
contentSlide("compression");
contentSlide("exercise");
contentSlide("lipedema_intro", { image: "lipedema_cuff", blocks: [0] });
contentSlide("lipedema_intro", { title: "Lipedema — Etiology & Misdiagnosis", blocks: [1, 2], image: null, noLead: true });

// lipedema stages, split 2 + 2
[[0, 2, "Lipedema Staging — Stages 1 & 2"], [2, 4, "Lipedema Staging — Stage 3 & Lipo-lymphedema"]]
  .forEach(([a, b, title], idx) => {
    const sec = S("lipedema_staging");
    const s = newSlide();
    head(s, sec.kicker, title);
    let y = idx === 0 ? lead(s, sec.lead, 1.72) : 1.85;
    const grp = sec.stages.slice(a, b);
    const cw = (CW - 0.3) / 2;
    const ch = idx === 1 ? 3.5 : 3.55;
    grp.forEach((st, i) => {
      const x = MX + i * (cw + 0.3);
      card(s, x, y, cw, ch);
      s.addShape(pres.ShapeType.roundRect, {
        x: x + 0.28, y: y + 0.2, w: 1.15, h: 0.36, fill: { color: P.teal },
        line: { color: P.teal, width: 0 }, rectRadius: 0.18,
      });
      s.addText(st.n.toUpperCase(), {
        x: x + 0.28, y: y + 0.2, w: 1.15, h: 0.36, fontSize: 11, bold: true,
        color: "FFFFFF", align: "center", valign: "middle", fontFace: "Calibri", margin: 0,
      });
      s.addText(st.h, {
        x: x + 1.55, y: y + 0.2, w: cw - 1.85, h: 0.36, fontSize: 14, bold: true,
        color: P.deep, fontFace: "Calibri", margin: 0, valign: "middle",
      });
      bullets(s, st.items, x + 0.28, y + 0.72, cw - 0.56, ch - 0.9, 11.5);
    });
    if (idx === 1) {
      s.addText(clean(sec.note), {
        x: MX, y: y + ch + 0.16, w: CW, h: 0.6, fontSize: 10.5, italic: true,
        color: P.rose, fontFace: "Calibri", margin: 0, valign: "top",
      });
    }
    s.addNotes(clean(sec.note));
  });

tableSlide("differential_lip", { colW: [2.6, 4.75, 4.76], size: 11, rowH: 0.33 });
contentSlide("lipedema_treatment");
contentSlide("red_flags");

// ============================================================ TAKEAWAYS
(function () {
  const sec = S("takeaways");
  const s = newSlide();
  head(s, sec.kicker, sec.title);
  const half = Math.ceil(sec.numbered.length / 2);
  [[0, half, MX], [half, sec.numbered.length, MX + CW / 2 + 0.15]].forEach(([a, b, x]) => {
    const runs = [];
    sec.numbered.slice(a, b).forEach((o, i, arr) => {
      runs.push({
        text: String(a + i + 1) + ".  ",
        options: { bold: true, fontSize: 13, color: P.teal, fontFace: "Calibri" },
      });
      runs.push({
        text: clean(o),
        options: {
          fontSize: 13, color: P.ink, fontFace: "Calibri",
          paraSpaceAfter: 9, breakLine: i < arr.length - 1,
        },
      });
    });
    s.addText(runs, { x, y: 1.7, w: CW / 2 - 0.15, h: 5.0, margin: 0, valign: "top" });
  });
  s.addNotes("Ten takeaways. If you are short on time, 3, 5 and 7 are the ones they must leave with.");
})();

// ============================================================ CLOSING
(function () {
  const s = newSlide(true);
  s.addText("Questions", {
    x: MX, y: 1.5, w: 8.4, h: 1.0, fontSize: 46, bold: true, color: "FFFFFF",
    fontFace: "Cambria", margin: 0, valign: "top",
  });
  s.addText("Scan for the full presentation, outline, and a 12-question self-check.", {
    x: MX, y: 2.65, w: 8.2, h: 0.6, fontSize: 16, color: "CBE6EB",
    fontFace: "Calibri", margin: 0, valign: "top",
  });
  s.addShape(pres.ShapeType.line, {
    x: MX, y: 3.6, w: 6.2, h: 0, line: { color: "3E7C8A", width: 1 },
  });
  s.addText(
    [{ text: M.presenter + ", " + M.presenter_creds, options: { bold: true, fontSize: 17, color: "FFFFFF", breakLine: true } },
     { text: M.org, options: { fontSize: 15, color: "CBE6EB", breakLine: true } },
     { text: M.address, options: { fontSize: 13, color: "A8CFD8", breakLine: true } },
     { text: M.phone + "   ·   " + M.website, options: { fontSize: 13, color: "A8CFD8" } }],
    { x: MX, y: 3.85, w: 8.2, h: 1.8, fontFace: "Calibri", margin: 0, valign: "top" }
  );
  s.addShape(pres.ShapeType.roundRect, {
    x: 9.7, y: 1.8, w: 3.05, h: 3.4, fill: { color: "FFFFFF" },
    line: { color: "FFFFFF", width: 0 }, rectRadius: 0.12,
  });
  s.addImage({ path: A("qr"), x: 10.05, y: 2.1, w: 2.35, h: 2.35 });
  s.addText(M.base_url.replace("https://", "") + M.pres_path, {
    x: 9.75, y: 4.55, w: 2.95, h: 0.55, fontSize: 7.5, color: P.slate,
    align: "center", fontFace: "Calibri", margin: 0,
  });
  s.addText(M.disclaimer, {
    x: MX, y: H - 0.7, w: CW, h: 0.4, fontSize: 10, italic: true,
    color: "7FA6B0", fontFace: "Calibri", margin: 0,
  });
  s.addNotes("Close here. Remind them the QR opens the quiz.");
})();

const out = path.join(HERE, "Lymphedema_Lipedema_TBTW.pptx");
pres.writeFile({ fileName: out }).then(() => {
  console.log("slides: " + n);
  console.log("captured photos used: " + PHOTOS_USED);
  console.log("optional/cuttable: " + (CUT.length ? "\n  " + CUT.join("\n  ") : "none"));
  console.log("wrote " + out);
});
