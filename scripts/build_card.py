"""
Builds the neofetch-style terminal card (assets/neofetch-dark.svg + assets/neofetch-light.svg)
from live GitHub data. Run locally with `python scripts/build_card.py` or let the
GitHub Action refresh it daily. Set GITHUB_TOKEN to avoid API rate limits.

Edit the PROFILE section below to change the static text.
"""
import http.client
import io
import json
import math
import os
import re
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

USER = "MaizaAymen"
ROOT = Path(__file__).resolve().parent.parent
WIDTH_CHARS = 60  # width of the right-hand info column, in characters
ROLE = "Full-Stack Engineer"  # caption under the portrait

# ── PROFILE (static lines) ─────────────────────────────────────────────
# ("key", "value") pairs; None = blank line; ("#", "Title") = section header
PROFILE = [
    ("OS", "Windows 10, Linux, Android"),
    ("Uptime", "{uptime}"),
    ("Host", "Tunisia"),
    ("Kernel", "Full-Stack & AI Software Engineer"),
    ("Focus", "Scalable APIs, LLM apps, Cloud-native"),
    ("IDE", "VS Code, IntelliJ IDEA, Android Studio"),
    None,
    ("Languages.Programming", "JavaScript, Python, Java, PHP"),
    ("Languages.Computer", "HTML, CSS, SQL, JSON, YAML"),
    ("Languages.Real", "Arabic, French, English"),
    None,
    ("Stack.Web", "Angular, React, Symfony, Spring Boot"),
    ("Stack.AI", "FastAPI, LangChain, Ollama, Streamlit"),
    ("Stack.Mobile", "Flutter, React Native"),
    ("Stack.Tools", "Docker, Git, MySQL, PostgreSQL"),
    None,
    ("#", "Contact"),
    ("Portfolio", "portfolio-teal-nine-41.vercel.app"),
    ("GitHub", "github.com/MaizaAymen"),
    None,
    ("#", "GitHub Stats"),
]

THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d", text="#c9d1d9",
                 key="#ffa657", value="#a5d6ff", dots="#484f58", ascii="#c9d1d9",
                 green="#3fb950", red="#f85149", bar_empty="#21262d"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de", text="#24292f",
                  key="#953800", value="#0a3069", dots="#afb8c1", ascii="#24292f",
                  green="#1a7f37", red="#cf222e", bar_empty="#eaeef2"),
}


# ── data ───────────────────────────────────────────────────────────────
def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": USER})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
            return body if "avatars" in url else json.loads(body)
        except (OSError, http.client.HTTPException):
            if attempt == 2:
                raise
            time.sleep(2)


def collect():
    user = api(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    commits = api(f"https://api.github.com/search/commits?q=author:{USER}")["total_count"]
    langs = Counter(r["language"] for r in own if r["language"])
    return dict(
        user=user,
        repos=user["public_repos"],
        own=len(own),
        forks=len(repos) - len(own),
        stars=sum(r["stargazers_count"] for r in repos),
        forked_by=sum(r["forks_count"] for r in own),
        commits=commits,
        followers=user["followers"],
        langs=langs.most_common(6),
        lang_total=sum(langs.values()),
        avatar=api(user["avatar_url"] + "&s=200" if "?" in user["avatar_url"] else user["avatar_url"] + "?s=200"),
    )


def uptime(created):
    start = datetime.fromisoformat(created.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    months = (now.year - start.year) * 12 + now.month - start.month
    if now.day < start.day:
        months -= 1
    anchor_m = start.month + months
    anchor = start.replace(year=start.year + (anchor_m - 1) // 12, month=(anchor_m - 1) % 12 + 1)
    days = (now - anchor).days
    y, m = divmod(months, 12)
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(days, 'day')}"


# ── code portrait ──────────────────────────────────────────────────────
# The portrait is drawn with this source code: every character is a pixel, and
# its opacity follows how dark the avatar is at that spot (hair, eyes and
# headphones come out strongest). Syntax colours are kept so it still reads as code.
CODE = """
const engineer = { name: "Maiza Aymen", role: "Full-Stack & AI Engineer", base: "Tunisia" };
const stack = { web: ["Angular", "React", "Symfony", "Spring Boot"], ai: ["FastAPI", "LangChain", "Ollama"],
  mobile: ["Flutter", "React Native"], data: ["PostgreSQL", "MySQL", "Kafka"], ops: ["Docker", "Git"] };
async function ship(idea) { const spec = await design(idea); const api = build(spec, stack.web);
  await test(api); return deploy(api, { ci: "github-actions", runtime: "docker" }); }
class Engineer { constructor(cfg) { this.cfg = cfg; this.coffee = Infinity; }
  learn(topic) { return this.cfg.skills.add(topic) && this; } solve(problem) { return problem
  .split("/").map((part) => this.learn(part)).reduce((a, b) => a + b, 0); } }
export default async function main() { while (true) { const idea = await inbox.next();
  if (idea.isWorthIt()) await ship(idea); else archive(idea); } }
"""
SYNTAX = re.compile(r'(?P<str>"[^"]*")|(?P<kw>\b(?:const|async|await|function|return|class|this|export|default|'
                    r'new|while|if|else|true|constructor)\b)|(?P<num>\b\d+\b|Infinity)|(?P<fn>\b\w+(?=\())|'
                    r'(?P<punct>[{}()\[\];,.:=>&+])')
CODE_COLORS = {
    "dark": dict(str="#a5d6ff", kw="#ff7b72", num="#79c0ff", fn="#d2a8ff", punct="#8b949e", id="#e6edf3",
                 accent="#9ecbff"),
    "light": dict(str="#0a3069", kw="#cf222e", num="#0550ae", fn="#8250df", punct="#57606a", id="#1f2328",
                  accent="#0969da"),
}


def code_stream():
    """Code characters with their syntax role, as one endless stream."""
    text = " ".join(CODE.split())
    roles = ["id"] * len(text)
    for m in SYNTAX.finditer(text):
        for i in range(m.start(), m.end()):
            roles[i] = m.lastgroup
    while True:
        yield from zip(text + " ", roles + ["id"])


def smoothstep(a, b, v):
    v = min(max((v - a) / (b - a), 0), 1)
    return v * v * (3 - 2 * v)


def code_portrait(png, theme, x0, y0, size, cols=74, rows=46):
    img = Image.open(io.BytesIO(png)).convert("RGB")
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=140)).resize((cols, rows), Image.LANCZOS)
    lum = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    border = [img.getpixel((x, 0)) for x in range(cols)] + [img.getpixel((0, y)) for y in range(rows)]
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    lh = size / rows
    colors = CODE_COLORS[theme]
    stream = code_stream()
    out = [f'<g font-size="{lh * 1.12:.2f}" font-weight="800">']
    for y in range(rows):
        spans, run, run_key = [], "", None
        for x in range(cols):
            ch, role = next(stream)
            # oval vignette + flat background -> faint "ghost" code; subject -> opacity by darkness
            d = math.hypot((x / cols - 0.5) / 0.5, (y / rows - 0.52) / 0.52)
            fade = min(max((1 - d) * 5, 0), 1)
            if math.dist(img.getpixel((x, y)), bg) < 45:
                fade = 0
            # three bands: background = ghost code, skin = mid, hair / eyes / headphones = full
            tone = smoothstep(0.2, 0.75, 1 - lum.getpixel((x, y)) / 255)
            opacity = 0.08 + fade * (0.3 + 0.62 * tone)
            level = round(opacity * 8)  # 9 opacity steps keep the file small
            # inside the subject, the darkest features switch to one accent colour so
            # the face reads as a shape rather than as scattered syntax colours
            if fade > 0.5 and tone > 0.55:
                role = "accent"
            key = (role, level)
            if key != run_key and run:
                spans.append((run, run_key))
                run = ""
            run, run_key = run + ch, key
        spans.append((run, run_key))
        body = "".join(f'<tspan fill="{colors[r]}" fill-opacity="{lv / 8:.3g}">{escape(s)}</tspan>'
                       for s, (r, lv) in spans)
        out.append(f'<text x="{x0}" y="{y0 + (y + 0.82) * lh:.1f}" textLength="{size:.1f}" '
                   f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{body}</text>')
    out.append("</g>")
    return out


# ── svg ────────────────────────────────────────────────────────────────
def info_lines(d):
    """Returns a list of lines; each line is a list of (text, role) spans."""
    login = f"{USER.lower()}@github"
    out = [[(login, "value"), (" " + "─" * (WIDTH_CHARS - len(login) - 1), "dots")]]
    for item in PROFILE:
        if item is None:
            out.append([(". ", "dots")])
        elif item[0] == "#":
            title = f"- {item[1]} "
            out.append([(title, "text"), ("─" * (WIDTH_CHARS - len(title)), "dots")])
        else:
            key, val = item
            val = val.format(uptime=uptime(d["user"]["created_at"]))
            fill = WIDTH_CHARS - len(key) - len(val) - 5
            out.append([(". ", "dots"), (key, "key"), (":", "text"),
                        (" " + "." * max(fill, 1) + " ", "dots"), (val, "value")])

    def pair(k1, v1, k2, v2, half=33):
        left = WIDTH_CHARS - half
        fill1 = half - len(k1) - len(v1) - 5
        fill2 = left - len(k2) - len(v2) - 6
        return [(". ", "dots"), (k1, "key"), (":", "text"), (" " + "." * max(fill1, 1) + " ", "dots"),
                (v1, "value"), (" | ", "text"), (k2, "key"), (":", "text"),
                (" " + "." * max(fill2, 1) + " ", "dots"), (v2, "value")]

    out.append(pair("Repos", f"{d['own']} {{Forked: {d['forks']}}}", "Stars", str(d["stars"])))
    out.append(pair("Commits", f"{d['commits']:,}", "Followers", str(d["followers"])))
    out.append(pair("Top lang", d["langs"][0][0], "Since", d["user"]["created_at"][:4]))
    return out


def render(d, theme):
    t = THEMES[theme]
    fs, lh, cw = 13, 18, 7.8  # font size, line height, monospace char width
    info = info_lines(d)
    pad = 28
    art_w = 340
    info_x = pad + art_w + 36
    width = int(info_x + WIDTH_CHARS * cw + pad)
    height = int(pad * 2 + 36 + len(info) * lh)
    art_y = pad + 36 + (len(info) * lh - art_w - 30) / 2

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" font-family="Consolas, \'SF Mono\', Menlo, \'DejaVu Sans Mono\', monospace" '
         f'font-size="{fs}">',
         "<style>"
         f".key{{fill:{t['key']}}}.value{{fill:{t['value']}}}.text{{fill:{t['text']}}}"
         f".dots{{fill:{t['dots']}}}.ascii{{fill:{t['ascii']}}}"
         # 'backwards' fill: lines stay visible in viewers that don't animate
         "@keyframes fade{from{opacity:0;transform:translateX(-6px)}}"
         ".ln{animation:fade .35s ease backwards}"
         "@keyframes blink{50%{opacity:0}}.cursor{animation:blink 1s step-end infinite}"
         "</style>",
         f'<rect width="{width}" height="{height}" rx="12" fill="{t["panel"]}" stroke="{t["border"]}"/>',
         # window chrome
         f'<circle cx="{pad}" cy="{pad}" r="6" fill="#ff5f56"/>'
         f'<circle cx="{pad + 20}" cy="{pad}" r="6" fill="#ffbd2e"/>'
         f'<circle cx="{pad + 40}" cy="{pad}" r="6" fill="#27c93f"/>',
         f'<text x="{width / 2}" y="{pad + 4}" text-anchor="middle" class="dots">{USER.lower()}@github: ~ $ neofetch</text>']

    # textLength pins every line to the grid whatever monospace font the viewer has
    fit = lambda n: f'textLength="{n * cw:.1f}" lengthAdjust="spacingAndGlyphs"'
    s += code_portrait(d["avatar"], theme, pad, art_y, art_w)
    # viewfinder corner brackets + caption around the portrait
    b, x1, y1, x2, y2 = 18, pad - 6, art_y - 6, pad + art_w + 6, art_y + art_w + 6
    s.append(f'<path d="M{x1} {y1 + b}V{y1}H{x1 + b}M{x2 - b} {y1}H{x2}V{y1 + b}'
             f'M{x2} {y2 - b}V{y2}H{x2 - b}M{x1 + b} {y2}H{x1}V{y2 - b}" '
             f'fill="none" stroke="{t["value"]}" stroke-width="1.5" opacity=".7"/>')
    s.append(f'<text x="{pad + art_w / 2}" y="{y2 + 24}" text-anchor="middle" class="dots" '
             f'letter-spacing="2">// {escape(d["user"]["name"].upper())} · {escape(ROLE.upper())}</text>')

    y0 = pad + 36 + lh * 0.75
    for i, spans in enumerate(info):
        y = y0 + i * lh
        delay = f'style="animation-delay:{i * 0.05:.2f}s"'
        parts = [f'<g class="ln" {delay}>']
        text_buf, col = [], 0
        for text, role in spans:
            text_buf.append(f'<tspan class="{role}">{escape(text)}</tspan>')
            col += len(text)
        parts.append(f'<text x="{info_x}" y="{y:.1f}" {fit(col)} xml:space="preserve">{"".join(text_buf)}</text>')
        parts.append("</g>")
        s.append("".join(parts))

    last = y0 + len(info) * lh
    s.append(f'<text x="{info_x}" y="{last:.1f}" class="value">$ <tspan class="cursor">█</tspan></text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    d = collect()
    (ROOT / "assets").mkdir(exist_ok=True)
    for theme in THEMES:
        (ROOT / "assets" / f"neofetch-{theme}.svg").write_text(render(d, theme), encoding="utf-8")
    print(f"ok: {d['own']} repos, {d['commits']} commits, {d['stars']} stars, langs={d['langs']}")


if __name__ == "__main__":
    main()
