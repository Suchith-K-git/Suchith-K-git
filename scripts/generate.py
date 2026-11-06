#!/usr/bin/env python3
"""Generates assets/snake.svg, assets/stats.svg and assets/trophies.svg from the public
GitHub profile page. Standard library only. Usage: python scripts/generate.py [username]"""
import os, re, sys, html, urllib.request
from datetime import date, timedelta, datetime, timezone

USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_USER", "Suchith-K-git")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = open(os.path.join(ROOT, "scripts", "fonts.css")).read()

BG, PANEL, LINE = "#080D1A", "#0C1428", "#1A2C57"
FG, MUT, ACC = "#F1F5FF", "#8A97B5", "#247BFF"
LEVELS = ["#111B36", "#14408F", "#1A5FD6", "#3C8CFF", "#9CC7FF"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 profile-generator"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

def esc(s): return html.escape(str(s), quote=True)

# ------------------------------------------------------------------ data
cal = get(f"https://github.com/users/{USER}/contributions")
prof = get(f"https://github.com/{USER}")

tips = {m.group(1): m.group(2) for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', cal)}
cells = []
for m in re.finditer(r"<td\b([^>]*)>", cal):
    a = m.group(1)
    d, i, l = re.search(r'data-date="([\d-]+)"', a), re.search(r'id="([^"]+)"', a), re.search(r'data-level="(\d)"', a)
    if not (d and i and l): continue
    pos = re.search(r"-(\d+)-(\d+)$", i.group(1))
    n = re.match(r"(\d+) contribution", tips.get(i.group(1), ""))
    cells.append(dict(date=d.group(1), row=int(pos.group(1)), col=int(pos.group(2)),
                      level=int(l.group(1)), count=int(n.group(1)) if n else 0))
if not cells: sys.exit("could not read contribution calendar")
cells.sort(key=lambda c: c["date"])
W = max(c["col"] for c in cells) + 1
total = sum(c["count"] for c in cells)

def counter(label):
    m = re.search(r'%s[\s\S]{0,200}?Counter[^>]*>\s*([\d,]+)' % label.capitalize(), prof)
    return m.group(1) if m else "0"
def people(label):
    m = re.search(r'>([\d,.k]+)</span>\s*%s' % label, prof)
    return m.group(1) if m else "0"
followers, following = people("followers"), people("following")
repos, starred = counter("repositories"), counter("stars")
# The public API is the reliable source for these counts (the HTML scrape breaks whenever GitHub
# changes its markup). It overrides the scraped values; the scrape stays as a fallback.
try:
    import json
    hdr = {"User-Agent": "profile-generator", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"): hdr["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    u = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/users/{USER}", headers=hdr), timeout=30))
    followers, following, repos = str(u["followers"]), str(u["following"]), str(u["public_repos"])
    print("counts from API:", followers, following, repos)
except Exception as e:
    print("API unavailable, using scraped counts:", e)
ach = []
for a in re.findall(r'alt="Achievement: ([^"]+)"', prof):
    if a not in ach: ach.append(a)

days = [c for c in cells if c["count"] > 0]
active = len(days)
best = max(cells, key=lambda c: c["count"])
longest = cur = 0; prev = None
for c in cells:
    if c["count"] > 0:
        cur = cur + 1 if prev and (date.fromisoformat(c["date"]) - prev).days == 1 else 1
        longest = max(longest, cur); prev = date.fromisoformat(c["date"])
    else:
        prev = None if True else prev; cur = 0
        prev = None
# current streak (a quiet "today" does not break it)
run = 0
for c in reversed(cells):
    if c["count"] > 0: run += 1
    elif c is cells[-1]: continue
    else: break
months = {}
for c in cells: months.setdefault(c["date"][:7], 0); months[c["date"][:7]] += c["count"]
MN = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

CSS = f"""<style>{FONTS}
.d{{font-family:'SKDisplay','Barlow Condensed','Arial Narrow',Impact,sans-serif;font-weight:700}}
.m{{font-family:'SKMono','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-weight:400}}
@keyframes fu{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.fu{{animation:fu .7s ease both}}
@media (prefers-reduced-motion:reduce){{.fu{{animation:none!important}}}}
"""
def svg(w, h, label, inner, extra_css="", defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><defs>{CSS}{extra_css}</style>{defs}</defs>'
            f'<rect width="{w}" height="{h}" rx="20" fill="{BG}"/>{inner}</svg>')
STAMP = datetime.now(timezone.utc).strftime("Updated %d %b %Y, %H:%M UTC")
def stamp(w, h): return f'<text x="{w-30}" y="{h-12}" text-anchor="end" class="m" font-size="11" fill="{MUT}">{STAMP}</text>'
def save(name, s):
    open(os.path.join(ASSETS, name), "w").write(s); print("wrote", name, len(s))

# ------------------------------------------------------------------ snake
P, S, X0, Y0 = 20, 16, 70, 84
dt, pad = 0.07, 8
path = [(-k, 0) for k in range(pad, 0, -1)]
for c in range(W):
    path += [(c, r) for r in (range(7) if c % 2 == 0 else range(6, -1, -1))]
last = path[-1]
path += [(last[0] + k, last[1]) for k in range(1, pad + 1)]
N = len(path); D = round(N * dt + 3, 2)
def xy(p): return (X0 + p[0] * P, Y0 + p[1] * P)
kf = ""
for k, p in enumerate(path):
    x, y = xy(p); kf += f"{k*dt/D*100:.3f}%{{transform:translate({x}px,{y}px)}}"
x, y = xy(path[-1]); kf += f"99.999%{{transform:translate({x}px,{y}px)}}"
x, y = xy(path[0]); kf += f"100%{{transform:translate({x}px,{y}px)}}"
css = f"@keyframes mv{{{kf}}}.sn{{animation:mv {D}s linear infinite}}"
index = {(c["col"], c["row"]): k + pad for k, p in enumerate(path) for c in [] }  # placeholder
arrive = {p: k for k, p in enumerate(path) if 0 <= p[0] < W}
grid = ""
for c in cells:
    x, y = X0 + c["col"] * P, Y0 + c["row"] * P
    col = LEVELS[c["level"]]
    if c["level"] > 0:
        pct = arrive[(c["col"], c["row"])] * dt / D * 100
        nm = f"e{c['col']}_{c['row']}"
        css += f"@keyframes {nm}{{0%,{pct:.3f}%{{fill:{col}}}{pct+0.01:.3f}%,100%{{fill:{LEVELS[0]}}}}}"
        grid += f'<rect x="{x}" y="{y}" width="{S}" height="{S}" rx="4" fill="{col}" style="animation:{nm} {D}s linear infinite"/>'
    else:
        grid += f'<rect x="{x}" y="{y}" width="{S}" height="{S}" rx="4" fill="{col}"/>'
body = ""
for i in range(7, -1, -1):
    op = max(0.25, 1 - i * 0.11); fill = ACC if i == 0 else FG
    stroke = f' stroke="{FG}" stroke-width="2"' if i == 0 else ""
    body += f'<rect class="sn" style="animation-delay:{i*dt:.2f}s" x="0" y="0" width="{S}" height="{S}" rx="5" fill="{fill}" opacity="{op:.2f}"{stroke}/>'
head = (f'<text x="48" y="50" class="d" font-size="32" fill="{FG}" letter-spacing="1">CONTRIBUTION SNAKE</text>'
        f'<rect x="48" y="60" width="40" height="3" fill="{ACC}"/>'
        f'<text x="1152" y="48" text-anchor="end" class="m" font-size="15" fill="{MUT}">{total} contributions in the last year</text>')
legend = f'<text x="1000" y="238" class="m" font-size="12" fill="{MUT}">Less</text>' + "".join(
    f'<rect x="{1035+i*20}" y="227" width="12" height="12" rx="3" fill="{LEVELS[i]}"/>' for i in range(5)) + f'<text x="1142" y="238" class="m" font-size="12" fill="{MUT}">More</text>'
save("snake.svg", svg(1200, 260, "Contribution snake", head + grid + body + legend, css))

# ------------------------------------------------------------------ stats
tiles = [("FOLLOWERS", followers), ("FOLLOWING", following), ("REPOSITORIES", repos), ("CONTRIBUTIONS", total)]
inner = ""
for i, (lab, val) in enumerate(tiles):
    x = 30 + i * 292
    inner += (f'<rect x="{x}" y="30" width="268" height="120" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
              f'<text x="{x+28}" y="98" class="d" font-size="64" fill="{ACC}">{esc(val)}</text>'
              f'<text x="{x+28}" y="130" class="m" font-size="14" fill="{MUT}" letter-spacing="2">{lab}</text>')
inner += f'<rect x="30" y="170" width="800" height="300" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
inner += f'<text x="58" y="208" class="d" font-size="26" fill="{FG}" letter-spacing="1">CONTRIBUTIONS PER MONTH</text><rect x="58" y="218" width="36" height="3" fill="{ACC}"/>'
ml = list(months.items())[-12:]
mx = max(v for _, v in ml) or 1
bw, gap, base, ch = 40, 22, 440, 170
for i, (k, v) in enumerate(ml):
    x = 62 + i * (bw + gap); h = max(4, int(v / mx * ch))
    inner += (f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" rx="6" fill="{ACC}" opacity="{0.45+0.55*v/mx:.2f}"/>'
              f'<text x="{x+bw/2}" y="{base-h-8}" text-anchor="middle" class="m" font-size="13" fill="{FG}">{v}</text>'
              f'<text x="{x+bw/2}" y="{base+20}" text-anchor="middle" class="m" font-size="12" fill="{MUT}">{MN[int(k[5:])-1]}</text>')
inner += f'<rect x="850" y="170" width="320" height="300" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
bd = date.fromisoformat(best["date"])
rows = [("ACTIVE DAYS", active), ("LONGEST STREAK", f"{longest} days"), ("CURRENT STREAK", f"{run} days"), ("BEST DAY", f"{best['count']}  ·  {bd.day} {MN[bd.month-1]}")]
for i, (l, v) in enumerate(rows):
    y = 214 + i * 64
    inner += f'<text x="880" y="{y}" class="m" font-size="13" fill="{MUT}" letter-spacing="2">{l}</text><text x="880" y="{y+32}" class="d" font-size="34" fill="{FG}" xml:space="preserve">{esc(v)}</text>'
save("stats.svg", svg(1200, 500, "GitHub statistics", inner + stamp(1200, 500)))

# ------------------------------------------------------------------ trophies & achievements
import math, textwrap
def num(v):
    v = str(v).lower().replace(",", "")
    try: return int(float(v[:-1]) * 1000) if v.endswith("k") else int(float(v))
    except ValueError: return 0
def hexagon(cx, cy, r):
    return " ".join(f"{cx + r*math.cos(math.radians(60*i-90)):.1f},{cy + r*math.sin(math.radians(60*i-90)):.1f}" for i in range(6))
ST = f'stroke="{FG}" stroke-width="3.2" fill="none" stroke-linecap="round" stroke-linejoin="round"'
def star(cx, cy, ro, ri):
    return " ".join(f"{cx + (ro if i%2==0 else ri)*math.cos(math.radians(36*i-90)):.1f},{cy + (ro if i%2==0 else ri)*math.sin(math.radians(36*i-90)):.1f}" for i in range(10))
def glyph(name, cx, cy):
    if name == "YOLO":
        return f'<path d="M{cx+4} {cy-22} L{cx-12} {cy+3} H{cx} L{cx-4} {cy+22} L{cx+14} {cy-4} H{cx+2} Z" {ST}/>'
    if name == "Starstruck":
        return f'<polygon points="{star(cx,cy,22,9)}" {ST}/>'
    if name == "Quickdraw":
        return f'<circle cx="{cx}" cy="{cy+3}" r="17" {ST}/><path d="M{cx} {cy+3} V{cy-8} M{cx-6} {cy-20} H{cx+6}" {ST}/>'
    if name == "Pull Shark":
        return (f'<circle cx="{cx-12}" cy="{cy-14}" r="5" {ST}/><circle cx="{cx-12}" cy="{cy+14}" r="5" {ST}/><circle cx="{cx+13}" cy="{cy+2}" r="5" {ST}/>'
                f'<path d="M{cx-12} {cy-9} V{cy+9} M{cx-12} {cy-2} C{cx-12} {cy+2} {cx+2} {cy+2} {cx+8} {cy+2}" {ST}/>')
    if name == "Pair Extraordinaire":
        return f'<circle cx="{cx-8}" cy="{cy-8}" r="7" {ST}/><circle cx="{cx+10}" cy="{cy-4}" r="6" {ST}/><path d="M{cx-20} {cy+20} a12 12 0 0 1 24 0 M{cx+2} {cy+20} a10 10 0 0 1 19 0" {ST}/>'
    if name == "Galaxy Brain":
        return f'<circle cx="{cx}" cy="{cy}" r="19" {ST}/><path d="M{cx-9} {cy+4} a9 9 0 1 1 18 0 a5 5 0 1 1 -10 0" {ST}/>'
    if name == "Arctic Code Vault Contributor":
        return f'<rect x="{cx-18}" y="{cy-18}" width="36" height="36" rx="5" {ST}/><circle cx="{cx}" cy="{cy}" r="8" {ST}/><path d="M{cx} {cy-8} V{cy-18} M{cx} {cy+8} V{cy+18}" {ST}/>'
    if name == "Heart On Your Sleeve":
        return f'<path d="M{cx} {cy+18} C{cx-28} {cy-2} {cx-14} {cy-24} {cx} {cy-8} C{cx+14} {cy-24} {cx+28} {cy-2} {cx} {cy+18} Z" {ST}/>'
    if name == "Open Sourcerer":
        return f'<path d="M{cx-12} {cy-12} L{cx-22} {cy} L{cx-12} {cy+12} M{cx+12} {cy-12} L{cx+22} {cy} L{cx+12} {cy+12} M{cx+4} {cy-18} L{cx-4} {cy+18}" {ST}/>'
    # any other / future achievement: a generic medal, so new badges render automatically
    return f'<circle cx="{cx}" cy="{cy-4}" r="14" {ST}/><path d="M{cx-8} {cy+8} L{cx-12} {cy+22} L{cx} {cy+16} L{cx+12} {cy+22} L{cx+8} {cy+8}" {ST}/>'
DESC = {"YOLO": "Merged a PR without review", "Starstruck": "Repo earned stars",
        "Quickdraw": "Closed an issue or PR in 5 minutes", "Pull Shark": "Opened PRs that got merged",
        "Pair Extraordinaire": "Co-authored a merged PR", "Galaxy Brain": "Answered a discussion",
        "Arctic Code Vault Contributor": "Code archived in the Arctic vault", "Heart On Your Sleeve": "Reacted with a heart",
        "Open Sourcerer": "Merged PRs in many public repos"}

# ---- achievements: auto-wrapped grid (4 per row), height follows the number of badges
PER = 4
rows_a = max(1, math.ceil(len(ach) / PER))
inner = f'<text x="48" y="58" class="d" font-size="30" fill="{FG}" letter-spacing="1">GITHUB ACHIEVEMENTS</text><rect x="48" y="68" width="40" height="3" fill="{ACC}"/>'
cw = (1104 - (PER - 1) * 20) / PER
for i, a in enumerate(ach):
    r_, c_ = divmod(i, PER)
    x = 48 + c_ * (cw + 20); y = 92 + r_ * 166; cx = x + 58; cy = y + 75
    lines = textwrap.wrap(DESC.get(a, "GitHub achievement"), 18)[:3]
    sub = "".join(f'<text x="{x+112}" y="{y+84+j*17}" class="m" font-size="12" fill="{MUT}">{esc(t)}</text>' for j, t in enumerate(lines))
    nm = esc(a if len(a) <= 14 else a[:13] + "…")
    inner += (f'<rect x="{x}" y="{y}" width="{cw}" height="150" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
              f'<polygon points="{hexagon(cx,cy,40)}" fill="{ACC}" fill-opacity=".16" stroke="{ACC}" stroke-width="2.5"/>{glyph(a,cx,cy)}'
              f'<text x="{x+112}" y="{y+56}" class="d" font-size="{32 if len(nm) <= 11 else 22}" fill="{FG}">{nm}</text>{sub}')
if not ach:
    inner += f'<text x="48" y="130" class="m" font-size="14" fill="{MUT}">No achievements unlocked yet.</text>'
TY = 92 + rows_a * 166 + 22   # trophies section top

# ---- trophies: tiered by real numbers, so the cup colour and level update automatically
TIERS = [("BRONZE", "#CD7F32"), ("SILVER", "#C9D3E6"), ("GOLD", "#FFC83D"), ("DIAMOND", "#5BD6FF")]
def tier(v, th):
    """returns (tier index or -1, next threshold or None)"""
    t = -1
    for k, need in enumerate(th):
        if v >= need: t = k
    nxt = th[t + 1] if t + 1 < len(th) else None
    return t, nxt
troph = [("FOLLOWERS", followers, num(followers), [1, 10, 50, 100]),
         ("REPOSITORIES", repos, num(repos), [1, 10, 25, 50]),
         ("CONTRIBUTIONS", total, total, [10, 100, 500, 1000]),
         ("LONGEST STREAK", f"{longest}d", longest, [2, 7, 14, 30]),
         ("ACTIVE DAYS", active, active, [5, 30, 100, 200]),
         ("BEST DAY", best["count"], best["count"], [3, 10, 25, 50])]
inner += f'<text x="48" y="{TY+30}" class="d" font-size="30" fill="{FG}" letter-spacing="1">TROPHIES</text><rect x="48" y="{TY+40}" width="40" height="3" fill="{ACC}"/>'
cw2 = (1104 - 5 * 16) / 6
CY = TY + 64
for i, (l, v, n, th) in enumerate(troph):
    x = 48 + i * (cw2 + 16); cx = x + cw2 / 2
    t, nxt = tier(n, th)
    tname, col = TIERS[t] if t >= 0 else ("LOCKED", "#4A5878")
    cup = f'stroke="{col}" stroke-width="3" fill="{col}" fill-opacity=".18" stroke-linecap="round" stroke-linejoin="round"'
    frac = 1 if nxt is None else max(0, min(1, (n - (th[t] if t >= 0 else 0)) / (nxt - (th[t] if t >= 0 else 0))))
    bx, bw_ = x + 24, cw2 - 48
    inner += (f'<rect x="{x}" y="{CY}" width="{cw2}" height="206" rx="16" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
              f'<g transform="translate({cx-18},{CY+18})"><path d="M6 2h24v14a12 12 0 0 1-24 0z M6 6H0v4a8 8 0 0 0 8 8 M30 6h6v4a8 8 0 0 1-8 8 M18 28v8 M10 40h16" {cup}/></g>'
              f'<text x="{cx}" y="{CY+112}" text-anchor="middle" class="d" font-size="48" fill="{FG}">{esc(v)}</text>'
              f'<text x="{cx}" y="{CY+138}" text-anchor="middle" class="m" font-size="12" fill="{MUT}" letter-spacing="1.5">{l}</text>'
              f'<rect x="{bx}" y="{CY+156}" width="{bw_}" height="5" rx="2.5" fill="{LINE}"/><rect x="{bx}" y="{CY+156}" width="{bw_*frac:.1f}" height="5" rx="2.5" fill="{col}"/>'
              f'<text x="{cx}" y="{CY+184}" text-anchor="middle" class="m" font-size="11" fill="{col}" letter-spacing="2">{tname}{"" if nxt is None else f"  ·  NEXT {nxt}"}</text>')
H = CY + 206 + 40
save("trophies.svg", svg(1200, H, "GitHub achievements and trophies", inner + stamp(1200, H)))
