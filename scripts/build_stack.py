#!/usr/bin/env python3
"""Builds assets/stack.svg: category rows of icon chips (Simple Icons, CC0).
Edit STACK below and run: python scripts/build_stack.py"""
import os, json, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = open(os.path.join(ROOT, "scripts", "fonts.css")).read()
ICONS = json.load(open(os.path.join(ROOT, "scripts", "icons.json")))
BG, PANEL, LINE, FG, MUT, ACC = "#080D1A", "#0C1428", "#1A2C57", "#F1F5FF", "#8A97B5", "#247BFF"
# brand colours too dark for the navy background are lightened
HEX = {"AWS": "FF9900", "Nexus": "4FB3FF", "Helm": "5C7CFA", "Trivy": "7B72FF", "Jira": "2684FF", "Kubernetes": "4C8DFF", "OWASP": "B8C4E0", "Git": "F4623A"}
STACK = [
    ("CLOUD & IAC",      [("AWS", "AWS"), ("Terraform", "Terraform")]),
    ("CONTAINERS",       [("Docker", "Docker"), ("Kubernetes", "Kubernetes"), ("Helm", "Helm")]),
    ("CI/CD & BUILD",    [("Jenkins", "Jenkins"), ("Maven", "Maven"), ("Nexus", "Nexus"), ("Git", "Git"), ("GitHub Actions", "GitHub Actions")]),
    ("DEVSECOPS",        [("SonarQube", "SonarQube"), ("Trivy", "Trivy"), ("OWASP", "OWASP Dependency-Check")]),
    ("MONITORING",       [("Prometheus", "Prometheus"), ("Grafana", "Grafana")]),
    ("SCRIPTING & OS",   [("Python", "Python"), ("Bash", "Shell Scripting"), ("Linux", "Linux"), ("Ansible", "Ansible")]),
    ("TRACKING",         [("Jira", "Jira")]),
]
W, X0, XC, ROW, TOP = 1200, 56, 290, 74, 100
CH, IC, CW = 48, 26, 8.6          # chip height, icon size, mono char width at 14px
esc = lambda s: html.escape(s, quote=True)
H = TOP + len(STACK) * ROW + 24
out = ""
for r, (cat, items) in enumerate(STACK):
    y = TOP + r * ROW
    out += f'<line x1="{X0}" y1="{y}" x2="{W-X0}" y2="{y}" stroke="{LINE}"/>'
    out += f'<text x="{X0}" y="{y+ROW/2+5}" class="m" font-size="14" fill="{ACC}" letter-spacing="2">{esc(cat)}</text>'
    x = XC
    for key, label in items:
        ic = ICONS[key]; col = "#" + HEX.get(key, ic["hex"]); w = 16 + IC + 10 + len(label) * CW + 16
        cy = y + (ROW - CH) / 2
        out += (f'<g class="fu" style="animation-delay:{r*0.08:.2f}s"><rect x="{x:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{CH}" rx="12" fill="{PANEL}" stroke="{LINE}" stroke-width="1.5"/>'
                f'<svg x="{x+16:.1f}" y="{cy+(CH-IC)/2:.1f}" width="{IC}" height="{IC}" viewBox="0 0 24 24"><path d="{ic["path"]}" fill="{col}"/></svg>'
                f'<text x="{x+16+IC+10:.1f}" y="{cy+CH/2+5:.1f}" class="m" font-size="14" fill="{FG}">{esc(label)}</text></g>')
        x += w + 12
    assert x - 12 <= W - X0, f"row {cat} overflows"
out += f'<line x1="{X0}" y1="{TOP+len(STACK)*ROW}" x2="{W-X0}" y2="{TOP+len(STACK)*ROW}" stroke="{LINE}"/>'
head = (f'<text x="{X0}" y="62" class="d" font-size="40" fill="{FG}">STACK</text><rect x="150" y="48" width="40" height="3" fill="{ACC}"/>')
css = f"""{FONTS}
.d{{font-family:'SKDisplay','Barlow Condensed','Arial Narrow',Impact,sans-serif;font-weight:700}}
.m{{font-family:'SKMono','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-weight:400}}
@keyframes fu{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.fu{{animation:fu .7s ease both}}
@media (prefers-reduced-motion:reduce){{.fu{{animation:none!important}}}}"""
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d"><title id="t">Technology stack</title>'
       f'<desc id="d">AWS, Terraform, Docker, Kubernetes, Jenkins, Maven, Nexus, SonarQube, Prometheus, Grafana, Python, Shell Scripting, Linux, Ansible and Jira.</desc>'
       f'<defs><style>{css}</style></defs><rect width="{W}" height="{H}" rx="18" fill="{BG}"/>{head}{out}</svg>')
open(os.path.join(ROOT, "assets", "stack.svg"), "w").write(svg); print("wrote stack.svg", len(svg), "h", H)
