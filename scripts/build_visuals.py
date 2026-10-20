"""
Builds the header banner and the architecture diagram (dark + light variants)
with real brand logos from Simple Icons, embedded as vector paths so GitHub
renders them (SVGs shown via <img> can't load external images).

Run once after editing: `python scripts/build_visuals.py`
"""
import re
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SI = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{}.svg"
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"
MONO = "Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', monospace"

# slug -> (label, brand colour)
LOGOS = {
    "angular": ("Angular", "#DD0031"), "react": ("React", "#61DAFB"), "flutter": ("Flutter", "#02569B"),
    "springboot": ("Spring Boot", "#6DB33F"), "symfony": ("Symfony", "#000000"), "fastapi": ("FastAPI", "#009688"),
    "nodedotjs": ("Node / Express", "#5FA04E"), "postgresql": ("PostgreSQL", "#4169E1"), "mysql": ("MySQL", "#4479A1"),
    "apachekafka": ("Kafka", "#231F20"), "langchain": ("LangChain", "#1C3C3C"), "ollama": ("Ollama", "#000000"),
    "python": ("Python", "#3776AB"), "docker": ("Docker", "#2496ED"), "git": ("Git", "#F05032"),
    "githubactions": ("GitHub Actions", "#2088FF"), "linux": ("Linux", "#FCC624"), "vercel": ("Vercel", "#000000"),
    "javascript": ("JavaScript", "#F7DF1E"), "typescript": ("TypeScript", "#3178C6"), "php": ("PHP", "#777BB4"),
    "dart": ("Dart", "#0175C2"), "streamlit": ("Streamlit", "#FF4B4B"), "openjdk": ("Java", "#ED8B00"),
}

THEMES = {
    "dark": dict(bg1="#0d1117", bg2="#161b22", card="#161b22", card2="#1c2330", border="#30363d", text="#e6edf3",
                 muted="#8b949e", accent="#58a6ff", accent2="#3fb950", grid="#21262d", glow="#1f6feb", invert="#e6edf3"),
    "light": dict(bg1="#ffffff", bg2="#f6f8fa", card="#ffffff", card2="#f6f8fa", border="#d0d7de", text="#1f2328",
                  muted="#59636e", accent="#0969da", accent2="#1a7f37", grid="#eaeef2", glow="#54aeff", invert="#1f2328"),
}


def fetch_paths():
    paths = {}
    for slug in LOGOS:
        with urllib.request.urlopen(SI.format(slug), timeout=30) as r:
            svg = r.read().decode()
        paths[slug] = re.search(r' d="([^"]+)"', svg).group(1)
    return paths


def is_near_black(hex_):
    return max(int(hex_[i:i + 2], 16) for i in (1, 3, 5)) < 0x40


def logo(paths, slug, x, y, size, t):
    """Simple Icons are drawn on a 24x24 grid. Near-black brands flip to the text colour in dark mode."""
    color = LOGOS[slug][1]
    if t["bg1"] == "#0d1117" and is_near_black(color):
        color = t["invert"]
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({size / 24:.3f})">'
            f'<path d="{paths[slug]}" fill="{color}"/></g>')


def defs(t):
    return (f'<defs>'
            f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1.2" fill="{t["grid"]}"/></pattern>'
            f'<linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="#58a6ff"/><stop offset=".55" stop-color="#a371f7"/>'
            f'<stop offset="1" stop-color="#3fb950"/></linearGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{t["glow"]}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{t["glow"]}" stop-opacity="0"/></radialGradient>'
            f'</defs>')


# ── banner ─────────────────────────────────────────────────────────────
def banner(paths, t):
    w, h = 1200, 280
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">',
         defs(t),
         "<style>"
         "@keyframes float{50%{transform:translateY(-5px)}}"
         ".tile{animation:float 4s ease-in-out infinite}"
         "@keyframes pulse{50%{opacity:.25}}.pulse{animation:pulse 1.8s ease-in-out infinite}"
         "@keyframes dash{to{stroke-dashoffset:-400}}.hex{stroke-dasharray:14 6;animation:dash 12s linear infinite}"
         "</style>",
         f'<rect width="{w}" height="{h}" rx="16" fill="{t["bg1"]}"/>',
         f'<rect width="{w}" height="{h}" rx="16" fill="url(#dots)"/>',
         f'<circle cx="190" cy="140" r="220" fill="url(#glow)"/>',
         f'<circle cx="1000" cy="140" r="240" fill="url(#glow)" opacity=".6"/>',
         f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>']

    # hexagon monogram
    cx, cy, R = 140, 140, 78
    pts = " ".join(f"{cx + R * c:.1f},{cy + R * s_:.1f}" for c, s_ in
                   [(0, -1), (0.866, -0.5), (0.866, 0.5), (0, 1), (-0.866, 0.5), (-0.866, -0.5)])
    s.append(f'<polygon points="{pts}" fill="{t["card"]}" stroke="url(#brand)" stroke-width="4" class="hex"/>')
    s.append(f'<text x="{cx}" y="{cy + 17}" text-anchor="middle" font-size="50" font-weight="800" '
             f'fill="url(#brand)" letter-spacing="-1">MA</text>')
    s.append(f'<text x="{cx}" y="{cy + 40}" text-anchor="middle" font-family="{MONO}" font-size="11" '
             f'fill="{t["muted"]}">&lt;/&gt;</text>')

    # name block
    x = 260
    s.append(f'<text x="{x}" y="112" font-size="52" font-weight="800" fill="{t["text"]}" letter-spacing="-1">Maiza Aymen</text>')
    s.append(f'<text x="{x}" y="150" font-size="22" font-weight="600" fill="url(#brand)">Software Engineering Student · Full-Stack &amp; AI</text>')
    s.append(f'<text x="{x}" y="184" font-family="{MONO}" font-size="14" fill="{t["muted"]}">'
             f'Web · APIs · LLM apps · Mobile · Cloud-native  —  Tunisia</text>')
    s.append(f'<circle cx="{x + 7}" cy="219" r="6" fill="{t["accent2"]}" class="pulse"/>')
    s.append(f'<text x="{x + 22}" y="224" font-family="{MONO}" font-size="14" fill="{t["accent2"]}">'
             f'open to internships &amp; collaboration</text>')

    # logo tiles, 2 rows x 5
    slugs = ["angular", "react", "springboot", "fastapi", "python",
             "langchain", "docker", "postgresql", "apachekafka", "flutter"]
    tile, gap, x0, y0 = 58, 14, 790, 68
    for i, slug in enumerate(slugs):
        r, c = divmod(i, 5)
        tx, ty = x0 + c * (tile + gap), y0 + r * (tile + gap)
        s.append(f'<g class="tile" style="animation-delay:{i * .25:.2f}s">'
                 f'<rect x="{tx}" y="{ty}" width="{tile}" height="{tile}" rx="14" fill="{t["card2"]}" stroke="{t["border"]}"/>'
                 + logo(paths, slug, tx + 15, ty + 15, 28, t) + "</g>")
    s.append(f'<text x="{x0 + (5 * tile + 4 * gap) / 2}" y="{y0 + 2 * tile + gap + 34}" text-anchor="middle" '
             f'font-family="{MONO}" font-size="12" fill="{t["muted"]}">// daily drivers</text>')
    s.append("</svg>")
    return "\n".join(s)


# ── architecture diagram ───────────────────────────────────────────────
COLUMNS = [
    # (node id, logo slug, label)
    ("01 · CLIENTS", [("angular", "angular", "Angular"), ("react", "react", "React"),
                      ("rn", "react", "React Native"), ("flutter", "flutter", "Flutter")]),
    ("02 · SERVICES / APIs", [("spring", "springboot", "Spring Boot"), ("symfony", "symfony", "Symfony"),
                              ("express", "nodedotjs", "Node · Express"), ("fastapi", "fastapi", "FastAPI")]),
    ("03 · DATA & EVENTS", [("postgres", "postgresql", "PostgreSQL"), ("mysql", "mysql", "MySQL"),
                            ("kafka", "apachekafka", "Kafka")]),
    ("04 · AI LAYER", [("langchain", "langchain", "LangChain"), ("ollama", "ollama", "Ollama · local LLM")]),
]
GAP_LABELS = ["HTTPS · REST/JSON", "SQL · events", ""]
# (from, to): who talks to whom
EDGES = [
    ("angular", "spring"), ("angular", "symfony"),
    ("react", "express"), ("react", "fastapi"), ("rn", "express"), ("flutter", "fastapi"),
    ("spring", "mysql"), ("spring", "kafka"), ("symfony", "mysql"),
    ("express", "postgres"), ("express", "kafka"), ("fastapi", "postgres"),
]
DEVOPS = ["docker", "git", "githubactions", "linux", "vercel"]


def architecture(paths, t):
    w, h = 1200, 576
    colw, nodeh, gapx, colh = 240, 54, 50, 300
    x0, ytop = 40, 140
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">',
         defs(t),
         "<style>"
         "@keyframes flow{to{stroke-dashoffset:-24}}"
         f".wire{{fill:none;stroke:{t['accent']};stroke-width:1.6;stroke-dasharray:6 6;animation:flow 1s linear infinite;opacity:.75}}"
         "</style>",
         f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         f'<path d="M0 0L10 5L0 10z" fill="{t["accent"]}"/></marker></defs>',
         f'<rect width="{w}" height="{h}" rx="16" fill="{t["bg1"]}"/>',
         f'<rect width="{w}" height="{h}" rx="16" fill="url(#dots)"/>',
         f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t["border"]}"/>',
         f'<text x="40" y="58" font-size="24" font-weight="800" fill="{t["text"]}">How I ship</text>',
         f'<text x="40" y="84" font-family="{MONO}" font-size="13" fill="{t["muted"]}">'
         f'// reference architecture behind my projects: client → API → data/events → AI</text>']

    nodes = {}  # id -> (left_x, right_x, top_y, center_y)
    for ci, (title, col_nodes) in enumerate(COLUMNS):
        cx = x0 + ci * (colw + gapx)
        s.append(f'<rect x="{cx - 12}" y="{ytop - 12}" width="{colw + 24}" height="{colh}" rx="14" '
                 f'fill="{t["card2"]}" fill-opacity=".55" stroke="{t["border"]}" stroke-dasharray="4 4"/>')
        s.append(f'<text x="{cx}" y="{ytop + 10}" font-family="{MONO}" font-size="12" font-weight="700" '
                 f'fill="{t["accent"]}" letter-spacing="1">{escape(title)}</text>')
        step = (colh - 40) / len(col_nodes)
        for ni, (nid, slug, label) in enumerate(col_nodes):
            ny = ytop + 28 + ni * step + (step - nodeh) / 2
            s.append(f'<rect x="{cx}" y="{ny:.1f}" width="{colw}" height="{nodeh}" rx="10" '
                     f'fill="{t["card"]}" stroke="{t["border"]}"/>')
            s.append(logo(paths, slug, cx + 14, ny + 13, 28, t))
            s.append(f'<text x="{cx + 56}" y="{ny + 33:.1f}" font-size="16" font-weight="600" '
                     f'fill="{t["text"]}">{escape(label)}</text>')
            nodes[nid] = (cx, cx + colw, ny, ny + nodeh / 2)

    # protocol labels over the gaps between columns
    for ci, label in enumerate(GAP_LABELS):
        gx = x0 + (ci + 1) * (colw + gapx) - gapx / 2
        s.append(f'<text x="{gx}" y="{ytop - 22}" text-anchor="middle" font-family="{MONO}" font-size="11" '
                 f'fill="{t["muted"]}">{escape(label)}</text>')

    # only the connections my projects actually use
    for a, b in EDGES:
        _, ax, _, ay = nodes[a]
        bx, _, _, by = nodes[b]
        mx = (ax + bx) / 2
        s.append(f'<path class="wire" d="M{ax} {ay:.1f}C{mx} {ay:.1f} {mx} {by:.1f} {bx - 4} {by:.1f}" '
                 f'marker-end="url(#arrow)"/>')
        s.append(f'<circle cx="{ax}" cy="{ay:.1f}" r="3.5" fill="{t["accent"]}"/>')

    # FastAPI -> LangChain skips the data column, so it runs on a bus under it
    _, ax, _, ay = nodes["fastapi"]
    bx, _, _, by = nodes["langchain"]
    bus = ytop + colh + 10
    s.append(f'<path class="wire" d="M{ax} {ay:.1f}H{ax + 18}Q{ax + 25} {ay:.1f} {ax + 25} {ay + 8:.1f}'
             f'V{bus - 8}Q{ax + 25} {bus} {ax + 33} {bus}H{bx - 33}Q{bx - 25} {bus} {bx - 25} {bus - 8}'
             f'V{by + 8:.1f}Q{bx - 25} {by:.1f} {bx - 17} {by:.1f}H{bx - 4}" marker-end="url(#arrow)"/>')
    s.append(f'<circle cx="{ax}" cy="{ay:.1f}" r="3.5" fill="{t["accent"]}"/>')
    s.append(f'<rect x="{(ax + bx) / 2 - 92}" y="{bus - 9}" width="184" height="18" rx="9" fill="{t["bg1"]}"/>'
             f'<text x="{(ax + bx) / 2}" y="{bus + 4}" text-anchor="middle" font-family="{MONO}" font-size="11" '
             f'fill="{t["muted"]}">prompts · RAG · tools</text>')

    # LangChain -> Ollama inside the AI column
    lx, rx, _, ly = nodes["langchain"]
    _, _, oy, _ = nodes["ollama"]
    mid = (lx + rx) / 2
    s.append(f'<path class="wire" d="M{mid} {ly + nodeh / 2:.1f}V{oy - 4:.1f}" marker-end="url(#arrow)"/>')
    s.append(f'<text x="{mid + 10}" y="{(ly + nodeh / 2 + oy) / 2 + 4:.1f}" font-family="{MONO}" font-size="11" '
             f'fill="{t["muted"]}">inference</text>')

    # devops rail
    ry = ytop + colh + 34
    s.append(f'<rect x="28" y="{ry}" width="{w - 56}" height="74" rx="14" fill="{t["card2"]}" stroke="{t["border"]}"/>')
    s.append(f'<text x="48" y="{ry + 43}" font-family="{MONO}" font-size="12" font-weight="700" '
             f'fill="{t["accent2"]}" letter-spacing="1">05 · DEVOPS &amp; DELIVERY</text>')
    for i, slug in enumerate(DEVOPS):
        lx = 290 + i * 180
        s.append(logo(paths, slug, lx, ry + 23, 28, t))
        s.append(f'<text x="{lx + 38}" y="{ry + 43}" font-size="15" font-weight="600" '
                 f'fill="{t["text"]}">{escape(LOGOS[slug][0])}</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    paths = fetch_paths()
    (ROOT / "assets").mkdir(exist_ok=True)
    for name, t in THEMES.items():
        (ROOT / "assets" / f"banner-{name}.svg").write_text(banner(paths, t), encoding="utf-8")
        (ROOT / "assets" / f"architecture-{name}.svg").write_text(architecture(paths, t), encoding="utf-8")
    print("ok:", len(paths), "logos")


if __name__ == "__main__":
    main()
