#!/usr/bin/env python3
"""content.json -> static site. Nothing a reader sees is hardcoded here."""
import json, os, re, shutil, html

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "content.json")))
M, P = C["meta"], C["palette"]
OUT = os.path.join(HERE, "site")
PRES = M["pres_path"].strip("/")


# ------------------------------------------------------------------ helpers
def md(s):
    """**bold** and *italic* -> HTML. Escapes everything else."""
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --deep:#%(deep)s; --teal:#%(teal)s; --mid:#%(mid)s; --sea:#%(seafoam)s;
  --slate:#%(slate)s; --mist:#%(mist)s; --line:#%(line)s; --ink:#%(ink)s;
  --amber:#%(amber)s; --rose:#%(rose)s;
}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%%}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
     color:var(--ink);background:var(--mist);line-height:1.65;font-size:16px}
.wrap{max-width:820px;margin:0 auto;padding:0 20px}
a{color:var(--teal)}

/* ---- header ---- */
.top{background:var(--deep);color:#fff;padding:16px 0;position:sticky;top:0;z-index:50;
     box-shadow:0 1px 8px rgba(0,0,0,.16)}
.top .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.top .brand{font-size:12px;letter-spacing:.14em;text-transform:uppercase;
            font-weight:700;color:#8FD3DE;text-decoration:none}
.top nav{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
.top nav a{color:#DCEEF2;text-decoration:none;font-size:13px;font-weight:600;
           padding:7px 12px;border-radius:8px;background:rgba(255,255,255,.09)}
.top nav a.on{background:#fff;color:var(--deep)}

/* ---- hero ---- */
.hero{background:var(--deep);color:#fff;padding:46px 0 52px}
.hero .kick{font-size:12px;letter-spacing:.16em;text-transform:uppercase;
            color:#8FD3DE;font-weight:700;margin-bottom:14px}
.hero h1{font-size:30px;line-height:1.24;font-weight:700;letter-spacing:-.015em}
.hero .sub{margin-top:14px;color:#CBE6EB;font-size:17px}
.hero .who{margin-top:24px;padding-top:20px;border-top:1px solid rgba(255,255,255,.2);
           font-size:15px;color:#E4F2F5}
.hero .who b{color:#fff}
.hero .who .cred{font-size:13px;color:#A8CFD8}

/* ---- QR ---- */
.qr{background:#fff;border-radius:18px;padding:26px 20px 22px;text-align:center;
    margin:0 auto;max-width:520px;box-shadow:0 6px 26px rgba(0,0,0,.13)}
.qr h2{font-size:15px;color:var(--deep);letter-spacing:.1em;text-transform:uppercase;
       margin-bottom:6px}
.qr p{font-size:13px;color:var(--slate);margin-bottom:16px}
.qr img{width:100%%;max-width:400px;height:auto;display:block;margin:0 auto}
.qr .url{margin-top:14px;font-size:12px;color:var(--slate);word-break:break-all;
         font-family:ui-monospace,Menlo,Consolas,monospace}
@media print{.qr img{max-width:300px}}

/* ---- content ---- */
main{padding:34px 0 70px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;
      padding:24px;margin-bottom:16px}
.kick{font-size:11px;letter-spacing:.14em;text-transform:uppercase;
      color:var(--teal);font-weight:700;margin-bottom:8px}
h2.sec{font-size:23px;color:var(--deep);font-weight:700;line-height:1.25;
       letter-spacing:-.01em;margin-bottom:12px}
.lead{font-size:16px;color:var(--slate);margin-bottom:18px}
h3.blk{font-size:15px;color:var(--deep);font-weight:700;margin:20px 0 9px}
ul.pts{list-style:none}
ul.pts li{position:relative;padding:6px 0 6px 20px;font-size:15px;
          border-bottom:1px solid var(--line)}
ul.pts li:last-child{border-bottom:none}
ul.pts li:before{content:"";position:absolute;left:2px;top:15px;width:6px;height:6px;
                 border-radius:50%%;background:var(--sea)}
ol.num{list-style:none;counter-reset:n}
ol.num li{counter-increment:n;position:relative;padding:10px 0 10px 40px;font-size:15px;
          border-bottom:1px solid var(--line)}
ol.num li:last-child{border-bottom:none}
ol.num li:before{content:counter(n);position:absolute;left:0;top:10px;width:26px;height:26px;
                 border-radius:50%%;background:var(--deep);color:#fff;font-size:13px;
                 font-weight:700;display:flex;align-items:center;justify-content:center}
.note{margin-top:18px;padding:14px 16px;background:var(--mist);
      border-radius:10px;font-size:14px;color:var(--slate)}
.note b{color:var(--deep)}
figure{margin:18px 0 4px}
figure img{width:100%%;height:auto;border-radius:10px;border:1px solid var(--line)}
figcaption{font-size:12px;color:var(--slate);margin-top:7px;font-style:italic}
.slot{margin:16px 0 4px;padding:16px;border:2px dashed var(--line);border-radius:10px;
      font-size:13px;color:var(--slate);text-align:center}
.slot b{display:block;color:var(--deep);font-size:12px;letter-spacing:.1em;
        text-transform:uppercase;margin-bottom:4px}
.stagetag{display:inline-block;background:var(--deep);color:#fff;font-size:12px;
          font-weight:700;letter-spacing:.08em;text-transform:uppercase;
          padding:5px 12px;border-radius:999px;margin-bottom:10px}

/* ---- tables ---- */
.tw{overflow-x:auto;margin:16px 0 4px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%%;min-width:520px;font-size:14px}
th{background:var(--deep);color:#fff;text-align:left;padding:11px 12px;
   font-size:13px;font-weight:700}
td{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:var(--mist)}
td:first-child{font-weight:700;color:var(--deep)}
.hint{font-size:12px;color:var(--slate);margin-top:6px;font-style:italic}

/* ---- stage cards ---- */
.stages{display:grid;gap:14px;margin-top:16px}
.stage{border:1px solid var(--line);border-radius:12px;padding:18px;background:#fff}
.stage .n{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
          color:#fff;background:var(--teal);display:inline-block;padding:4px 11px;
          border-radius:999px;margin-bottom:8px}
.stage h4{font-size:17px;color:var(--deep);margin-bottom:10px}

/* ---- pillars ---- */
.pillars{display:grid;gap:12px;margin-top:16px}
@media(min-width:640px){.pillars{grid-template-columns:1fr 1fr}}
.pill{background:var(--deep);color:#fff;border-radius:12px;padding:18px}
.pill .n{width:30px;height:30px;border-radius:50%%;background:#fff;color:var(--deep);
         font-weight:700;display:flex;align-items:center;justify-content:center;
         margin-bottom:10px;font-size:15px}
.pill h4{font-size:16px;margin-bottom:6px}
.pill p{font-size:13.5px;color:#CBE6EB}

/* ---- quiz ---- */
.q{background:#fff;border:1px solid var(--line);border-radius:12px;margin-bottom:12px;
   overflow:hidden}
.q .qq{padding:18px;font-size:15.5px;font-weight:600;color:var(--ink)}
.q .qn{display:inline-block;background:var(--teal);color:#fff;font-size:12px;
       font-weight:700;width:24px;height:24px;border-radius:50%%;text-align:center;
       line-height:24px;margin-right:9px}
.q button{width:100%%;border:none;background:var(--mist);color:var(--deep);
          font-size:14px;font-weight:700;padding:13px;cursor:pointer;
          border-top:1px solid var(--line);font-family:inherit;text-align:center}
.q button:hover{background:#E6F1F3}
.q .qa{display:none;padding:18px;background:#F2F9FA;font-size:15px;color:var(--slate);
       border-top:1px solid var(--line)}
.q.open .qa{display:block}
.q.open button{background:var(--deep);color:#fff}
.qbar{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.qbar button{flex:1;min-width:130px;border:1px solid var(--line);background:#fff;
             color:var(--deep);font-weight:700;font-size:13.5px;padding:11px;
             border-radius:9px;cursor:pointer;font-family:inherit}
.qbar button:hover{background:var(--mist)}

/* ---- outline / hub ---- */
.olist{list-style:none;counter-reset:o}
.olist li{counter-increment:o;border-bottom:1px solid var(--line)}
.olist li:last-child{border-bottom:none}
.olist a{display:flex;gap:14px;align-items:baseline;padding:13px 4px;
         text-decoration:none;color:var(--ink)}
.olist a:hover{background:var(--mist)}
.olist .on{color:var(--teal);font-weight:700;font-size:13px;min-width:26px}
.olist .ot{font-weight:600;font-size:15.5px}
.olist .od{font-size:13px;color:var(--slate);margin-top:2px}
.olist .cut{font-size:11px;color:var(--amber);font-weight:700;letter-spacing:.06em;
            text-transform:uppercase;margin-left:6px}
.pcard{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;
       padding:22px;text-decoration:none;color:var(--ink);margin-bottom:14px}
.pcard:hover{border-color:var(--teal)}
.pcard h3{font-size:19px;color:var(--deep);margin-bottom:6px}
.pcard p{font-size:14px;color:var(--slate)}
.pcard .go{margin-top:12px;font-size:13px;font-weight:700;color:var(--teal)}

/* ---- capabilities ---- */
.cap{margin-bottom:16px}
.cap .badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.09em;
            text-transform:uppercase;padding:4px 10px;border-radius:999px;margin-bottom:12px}
.b-live{background:#E1F5EF;color:#046B5D}
.b-ready{background:#E3EEF6;color:#1C5A85}
.b-service{background:#FBEEDA;color:#8A5606}
.b-avoid{background:#FAE7EC;color:#8C2F4C}
.cap dl{margin-top:4px}
.cap dt{font-weight:700;font-size:14.5px;color:var(--deep);margin-top:13px}
.cap dd{font-size:14px;color:var(--slate);margin-top:2px}

footer{border-top:1px solid var(--line);padding:26px 0 50px;font-size:13px;color:#6B7C84}
footer b{color:var(--slate)}
footer .dis{margin-top:8px;font-style:italic}
@media(min-width:700px){.hero h1{font-size:38px}h2.sec{font-size:26px}}
@media print{.top,.qbar{display:none}.q .qa{display:block}.card{break-inside:avoid}}
""" % P


def page(title, body, active, depth=0):
    up = "../" * depth
    nav = [("Home", up + "index.html", "home"),
           ("Presentation", up + PRES + "/index.html", "pres"),
           ("Outline", up + PRES + "/outline.html", "outline"),
           ("Quiz", up + PRES + "/quiz.html", "quiz"),
           ("Capabilities", up + "capabilities.html", "cap")]
    links = "".join(
        f'<a href="{h}" class="{"on" if k == active else ""}">{n}</a>' for n, h, k in nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(M['title'])} — {html.escape(M['org'])}">
<style>{CSS}</style>
</head><body>
<header class="top"><div class="wrap">
<a href="{up}index.html" class="brand">{html.escape(M['org'])}</a>
<nav>{links}</nav>
</div></header>
{body}
<footer><div class="wrap">
<b>{html.escape(M['org'])}</b> &middot; {html.escape(M['address'])} &middot; {html.escape(M['phone'])}
<div class="dis">{html.escape(M['disclaimer'])}</div>
</div></footer>
</body></html>"""


# ------------------------------------------------------------ section render
def render_section(s, depth=1):
    o = ['<section class="card" id="%s">' % s["id"]]
    if s.get("kicker"):
        o.append('<div class="kick">%s</div>' % md(s["kicker"]))
    if s.get("stage_label"):
        o.append('<span class="stagetag">%s</span>' % md(s["stage_label"]))
    o.append('<h2 class="sec">%s</h2>' % md(s["title"]))
    if s.get("lead"):
        o.append('<p class="lead">%s</p>' % md(s["lead"]))

    if s.get("diagram"):
        o.append('<figure><img src="%sassets/%s.png" alt="%s" loading="lazy">'
                 '</figure>' % ("../" * depth, s["diagram"], md(s["title"])))

    for b in s.get("blocks", []):
        o.append('<h3 class="blk">%s</h3><ul class="pts">' % md(b["h"]))
        o += ["<li>%s</li>" % md(i) for i in b["items"]]
        o.append("</ul>")

    if s.get("pillars"):
        o.append('<div class="pillars">')
        for p in s["pillars"]:
            o.append('<div class="pill"><div class="n">%s</div><h4>%s</h4><p>%s</p></div>'
                     % (md(p["n"]), md(p["h"]), md(p["d"])))
        o.append("</div>")

    if s.get("stages"):
        o.append('<div class="stages">')
        for st in s["stages"]:
            o.append('<div class="stage"><span class="n">%s</span><h4>%s</h4><ul class="pts">'
                     % (md(st["n"]), md(st["h"])))
            o += ["<li>%s</li>" % md(i) for i in st["items"]]
            o.append("</ul></div>")
        o.append("</div>")

    if s.get("table"):
        t = s["table"]
        o.append('<div class="tw"><table><thead><tr>')
        o += ["<th>%s</th>" % md(c) for c in t["cols"]]
        o.append("</tr></thead><tbody>")
        for r in t["rows"]:
            o.append("<tr>" + "".join("<td>%s</td>" % md(c) for c in r) + "</tr>")
        o.append("</tbody></table></div>")
        o.append('<p class="hint">Scroll the table sideways on a phone.</p>')

    if s.get("numbered"):
        o.append('<ol class="num">')
        o += ["<li>%s</li>" % md(i) for i in s["numbered"]]
        o.append("</ol>")

    if s.get("photo_slot"):
        o.append('<div class="slot"><b>Clinical photo</b>%s</div>' % md(s["photo_slot"]))

    if s.get("note"):
        o.append('<div class="note">%s</div>' % md(s["note"]))
    o.append("</section>")
    return "\n".join(o)


# ------------------------------------------------------------------- pages
def build_presentation():
    url = M["base_url"].rstrip("/") + M["pres_path"]
    body = ['<div class="hero"><div class="wrap">',
            '<div class="kick">%s</div>' % md(M["org"]),
            "<h1>%s</h1>" % md(M["title"]),
            '<p class="sub">%s</p>' % md(M["subtitle"]),
            '<div class="who"><b>%s</b>, %s<br><span class="cred">%s</span></div>'
            % (md(M["presenter"]), md(M["presenter_creds"]), md(M["presenter_role"])),
            "</div></div>",
            '<main class="wrap">',
            '<div class="qr"><h2>Follow along</h2>'
            "<p>Scan to open this presentation on your own device</p>"
            '<img src="../assets/qr.svg" alt="QR code linking to this presentation">'
            '<div class="url">%s</div></div>' % html.escape(url)]

    ab = C["about_org"]
    body.append('<section class="card" id="about"><div class="kick">About</div>'
                '<h2 class="sec">%s</h2><p class="lead">%s</p><ul class="pts">%s</ul></section>'
                % (md(ab["heading"]), md(ab["body"]),
                   "".join("<li>%s</li>" % md(i) for i in ab["points"])))

    body.append('<section class="card" id="objectives"><div class="kick">Objectives</div>'
                '<h2 class="sec">On completion you will be able to</h2>'
                '<ol class="num">%s</ol></section>'
                % "".join("<li>%s</li>" % md(o) for o in C["objectives"]))

    for s in C["sections"]:
        body.append(render_section(s, depth=1))

    body.append('<section class="card"><div class="kick">References</div>'
                '<h2 class="sec">Sources</h2><ul class="pts">%s</ul></section>'
                % "".join("<li><strong>%s</strong> — %s <em>%s</em></li>"
                          % (md(a), md(b), md(c)) for a, b, c in C["sources"]))
    body.append("</main>")
    return page(M["title"] + " — " + M["org"], "\n".join(body), "pres", depth=1)


def build_outline():
    rows = [("About " + M["org_short"], "#about", "Presenter and practice", False),
            ("Objectives", "#objectives", "What you will be able to do", False)]
    for s in C["sections"]:
        label = s["title"]
        if s.get("stage_label"):
            label = s["stage_label"] + " — " + s["title"]
        rows.append((label, "#" + s["id"], s.get("lead") or s.get("kicker") or "",
                     s.get("cuttable", False)))

    items = []
    for i, (t, h, d, cut) in enumerate(rows, 1):
        d = re.sub(r"\*\*(.+?)\*\*", r"\1", d)
        d = (d[:110] + "…") if len(d) > 110 else d
        cutmark = '<span class="cut">optional</span>' if cut else ""
        items.append(
            '<li><a href="index.html%s"><span class="on">%d</span><span>'
            '<span class="ot">%s</span>%s<div class="od">%s</div></span></a></li>'
            % (h, i, md(t), cutmark, md(d)))

    n_cut = sum(1 for r in rows if r[3])
    body = f"""<div class="hero"><div class="wrap">
<div class="kick">{md(M['org'])}</div>
<h1>Outline</h1>
<p class="sub">{md(M['title'])} — {md(M['subtitle'])}</p>
</div></div>
<main class="wrap">
<section class="card">
<div class="kick">Agenda · {len(rows)} sections</div>
<h2 class="sec">Jump to any section</h2>
<p class="lead">Sections marked <em>optional</em> can be skipped without breaking the
flow — {n_cut} of {len(rows)}.</p>
<ul class="olist">{''.join(items)}</ul>
</section>
<section class="card">
<div class="kick">Audience</div>
<h2 class="sec">Who this is for</h2>
<p class="lead">{md(M['audience'])}</p>
</section>
</main>"""
    return page("Outline — " + M["title"], body, "outline", depth=1)


def build_quiz():
    qs = []
    for i, q in enumerate(C["quiz"], 1):
        qs.append(
            '<div class="q" id="q%d"><div class="qq"><span class="qn">%d</span>%s</div>'
            '<button type="button" data-q="%d">Show answer</button>'
            '<div class="qa">%s</div></div>' % (i, i, md(q["q"]), i, md(q["a"])))

    js = """
<script>
function setOpen(el,open){
  el.classList.toggle('open',open);
  el.querySelector('button').textContent = open ? 'Hide answer' : 'Show answer';
}
document.querySelectorAll('.q button').forEach(function(b){
  b.addEventListener('click',function(){
    var c=b.closest('.q'); setOpen(c,!c.classList.contains('open'));
  });
});
document.getElementById('all').addEventListener('click',function(){
  document.querySelectorAll('.q').forEach(function(c){setOpen(c,true);});
});
document.getElementById('none').addEventListener('click',function(){
  document.querySelectorAll('.q').forEach(function(c){setOpen(c,false);});
});
</script>"""

    body = f"""<div class="hero"><div class="wrap">
<div class="kick">{md(M['org'])}</div>
<h1>Self-check</h1>
<p class="sub">{len(C['quiz'])} questions. Think it through, then tap to reveal.</p>
</div></div>
<main class="wrap">
<div class="qbar">
<button type="button" id="all">Show all answers</button>
<button type="button" id="none">Hide all answers</button>
</div>
{''.join(qs)}
<section class="card"><div class="note">Answers reflect the ISL 2023 consensus and
current lipedema staging. Where the literature is genuinely divided — notably lipedema
Stage 4 — the answer says so.</div></section>
</main>{js}"""
    return page("Self-check quiz — " + M["title"], body, "quiz", depth=1)


def build_capabilities():
    cap = C["capabilities"]
    badge = {"live": "b-live", "ready": "b-ready",
             "service": "b-service", "avoid": "b-avoid"}
    label = {"live": "Working now", "ready": "Can be added",
             "service": "Needs a form service", "avoid": "Not recommended"}
    out = []
    for g in cap["groups"]:
        dl = "".join("<dt>%s</dt><dd>%s</dd>" % (md(a), md(b)) for a, b in g["items"])
        note = '<div class="note">%s</div>' % md(g["note"]) if g.get("note") else ""
        out.append('<section class="card cap"><span class="badge %s">%s</span>'
                   '<h2 class="sec">%s</h2><dl>%s</dl>%s</section>'
                   % (badge[g["state"]], label[g["state"]], md(g["h"]), dl, note))

    h = cap["hosting"]
    out.append('<section class="card cap"><h2 class="sec">%s</h2><dl>%s</dl></section>'
               % (md(h["h"]),
                  "".join("<dt>%s</dt><dd>%s</dd>" % (md(a), md(b)) for a, b in h["items"])))

    body = f"""<div class="hero"><div class="wrap">
<div class="kick">{md(M['org'])}</div>
<h1>Site capabilities</h1>
<p class="sub">{md(cap['lead'])}</p>
</div></div>
<main class="wrap">{''.join(out)}</main>"""
    return page("Capabilities — " + M["org"], body, "cap", depth=0)


def build_hub():
    n = len(C["sections"])
    body = f"""<div class="hero"><div class="wrap">
<div class="kick">{md(M['org'])}</div>
<h1>Presentations</h1>
<p class="sub">Clinical education from {md(M['org'])}.</p>
</div></div>
<main class="wrap">
<a class="pcard" href="{PRES}/index.html">
<h3>{md(M['title'])}</h3>
<p>{md(M['subtitle'])}</p>
<p class="go">{n} sections &middot; outline &middot; {len(C['quiz'])}-question self-check &rarr;</p>
</a>
<section class="card">
<div class="kick">About this site</div>
<h2 class="sec">How it works</h2>
<p class="lead">Each presentation lives in its own folder with a presentation page,
an outline, and a self-check quiz. New presentations are added as new folders without
changing anything here.</p>
<ul class="pts">
<li>Present live from any device; the audience follows along by scanning the QR code</li>
<li>Every page prints or saves to PDF from the browser</li>
<li>See <a href="capabilities.html">Capabilities</a> for what else this site can do</li>
</ul>
</section>
</main>"""
    return page(M["org"] + " — Presentations", body, "home", depth=0)


# -------------------------------------------------------------------- write
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, PRES), exist_ok=True)
    shutil.copytree(os.path.join(HERE, "assets"), os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    files = {
        "index.html": build_hub(),
        "capabilities.html": build_capabilities(),
        PRES + "/index.html": build_presentation(),
        PRES + "/outline.html": build_outline(),
        PRES + "/quiz.html": build_quiz(),
    }
    for path, txt in files.items():
        full = os.path.join(OUT, path)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print("  %-28s %6d bytes" % (path, len(txt.encode())))
    print("\nSite -> " + OUT)


if __name__ == "__main__":
    main()
