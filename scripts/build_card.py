"""
Builds the header card (assets/neofetch-dark.svg + assets/neofetch-light.svg):
a portrait drawn with lines of code, next to a rotating programming quote.
Run locally with `python scripts/build_card.py` or let the GitHub Action refresh
it daily (picks up a new avatar automatically). GITHUB_TOKEN avoids rate limits.

Edit QUOTES below to change the quotes.
"""
import http.client
import io
import json
import math
import os
import re
import textwrap
import time
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

USER = "MaizaAymen"
ROOT = Path(__file__).resolve().parent.parent
NAME = "Aymen Maiza"
TAGLINE = "Software Engineering Student · Full-Stack & AI"
ROLE = "Engineering Student"  # caption under the portrait

# (quote, author) — shown one after another; the first one is what non-animating viewers see
QUOTES = [
    ("First, solve the problem.\nThen, write the code.", "John Johnson"),
    ("Simplicity is prerequisite for reliability.", "Edsger W. Dijkstra"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
]
SECONDS_PER_QUOTE = 6

THEMES = {
    "dark": dict(panel="#161b22", border="#30363d", text="#e6edf3", muted="#8b949e",
                 faint="#484f58", accent="#58a6ff", prompt="#3fb950"),
    "light": dict(panel="#f6f8fa", border="#d0d7de", text="#1f2328", muted="#59636e",
                  faint="#afb8c1", accent="#0969da", prompt="#1a7f37"),
}
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"
MONO = "Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', monospace"


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
    sep = "&" if "?" in user["avatar_url"] else "?"
    return dict(user=user, avatar=api(f"{user['avatar_url']}{sep}s=200"))


# ── code portrait ──────────────────────────────────────────────────────
# The portrait is drawn with this source code: every character is a pixel, and
# its opacity follows how dark the avatar is at that spot (hair, eyes and
# headphones come out strongest). Syntax colours are kept so it still reads as code.
CODE = """
const engineer = { name: "Maiza Aymen", role: "Software Engineering Student", base: "Tunisia" };
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


def code_portrait(png, theme, x0, y0, size, cols=64, rows=40):
    img = Image.open(io.BytesIO(png)).convert("RGB")
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=140)).resize((cols, rows), Image.LANCZOS)
    lum = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    border = [img.getpixel((x, 0)) for x in range(cols)] + [img.getpixel((0, y)) for y in range(rows)]
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    lh = size / rows
    colors = CODE_COLORS[theme]
    stream = code_stream()
    out = [f'<g font-family="{MONO}" font-size="{lh * 1.12:.2f}" font-weight="800">']
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
def quote_block(t, x, y, text, author):
    # "\n" in a quote forces a break; longer parts wrap on their own
    lines = [line for part in text.split("\n") for line in textwrap.wrap(part, 34)]
    out = [f'<text x="{x - 4}" y="{y + 40}" font-family="Georgia, serif" font-size="54" fill="{t["accent"]}" '
           f'opacity=".35">“</text>']
    for i, line in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + 56 + i * 29}" font-family="{SANS}" font-size="22" font-weight="600" '
                   f'fill="{t["text"]}">{escape(line)}</text>')
    ay = y + 56 + len(lines) * 29 + 6
    out.append(f'<rect x="{x}" y="{ay - 4}" width="28" height="2" fill="{t["accent"]}"/>'
               f'<text x="{x + 38}" y="{ay + 2}" font-family="{SANS}" font-size="15" fill="{t["muted"]}">'
               f'{escape(author)}</text>')
    return out


def render(d, theme):
    t = THEMES[theme]
    w, h, pad = 820, 352, 24
    art = 236
    art_x, art_y = pad + 8, 66
    qx = art_x + art + 48
    n, period = len(QUOTES), SECONDS_PER_QUOTE * len(QUOTES)
    slot = 100 / n

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
         f'font-family="{MONO}">',
         "<style>",
         # quote i is visible during its slot; quote 0 is visible by default so non-animating
         # viewers still see one quote, the others start hidden
         f"@keyframes q0{{0%,{slot - 4:.1f}%{{opacity:1}}{slot:.1f}%,{100 - 4:.1f}%{{opacity:0}}100%{{opacity:1}}}}",
         *[f".q{i}{{opacity:0;animation:qi{i} {period}s infinite}}"
           f"@keyframes qi{i}{{0%,{i * slot:.1f}%{{opacity:0}}{i * slot + 4:.1f}%,{(i + 1) * slot - 4:.1f}%{{opacity:1}}"
           f"{(i + 1) * slot:.1f}%,100%{{opacity:0}}}}" for i in range(1, n)],
         f".q0{{animation:q0 {period}s infinite}}",
         "@keyframes blink{50%{opacity:0}}.cursor{animation:blink 1s step-end infinite}",
         "</style>",
         f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["panel"]}" stroke="{t["border"]}"/>',
         f'<circle cx="{pad + 4}" cy="{pad + 4}" r="6" fill="#ff5f56"/>'
         f'<circle cx="{pad + 24}" cy="{pad + 4}" r="6" fill="#ffbd2e"/>'
         f'<circle cx="{pad + 44}" cy="{pad + 4}" r="6" fill="#27c93f"/>',
         f'<text x="{w / 2}" y="{pad + 8}" text-anchor="middle" font-size="13" fill="{t["faint"]}">'
         f'{USER.lower()}@github: ~ $ cat motto.md</text>']

    s += code_portrait(d["avatar"], theme, art_x, art_y, art)
    b, x1, y1, x2, y2 = 14, art_x - 6, art_y - 6, art_x + art + 6, art_y + art + 6
    s.append(f'<path d="M{x1} {y1 + b}V{y1}H{x1 + b}M{x2 - b} {y1}H{x2}V{y1 + b}'
             f'M{x2} {y2 - b}V{y2}H{x2 - b}M{x1 + b} {y2}H{x1}V{y2 - b}" '
             f'fill="none" stroke="{t["accent"]}" stroke-width="1.5" opacity=".7"/>')
    s.append(f'<text x="{art_x + art / 2}" y="{y2 + 20}" text-anchor="middle" font-size="11" fill="{t["faint"]}" '
             f'letter-spacing="1">// {escape(NAME.upper())} · {escape(ROLE.upper())}</text>')

    # name + role, then the rotating quote underneath
    s.append('<defs><linearGradient id="name" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="#58a6ff"/><stop offset=".55" stop-color="#a371f7"/>'
             '<stop offset="1" stop-color="#3fb950"/></linearGradient></defs>')
    s.append(f'<text x="{qx}" y="98" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-1" '
             f'fill="url(#name)">{escape(NAME)}</text>')
    s.append(f'<text x="{qx}" y="124" font-size="13" fill="{t["muted"]}">{escape(TAGLINE)}</text>')
    s.append(f'<rect x="{qx}" y="140" width="{w - qx - 40}" height="1" fill="{t["border"]}"/>')
    for i, (text, author) in enumerate(QUOTES):
        s.append(f'<g class="q{i}">' + "".join(quote_block(t, qx, 146, text, author)) + "</g>")

    s.append(f'<text x="{qx}" y="{h - 34}" font-size="14" fill="{t["prompt"]}">$ <tspan fill="{t["muted"]}">'
             f'keep shipping</tspan> <tspan class="cursor" fill="{t["accent"]}">█</tspan></text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    d = collect()
    (ROOT / "assets").mkdir(exist_ok=True)
    for theme in THEMES:
        (ROOT / "assets" / f"neofetch-{theme}.svg").write_text(render(d, theme), encoding="utf-8")
    print("ok: header card with", len(QUOTES), "quotes")


if __name__ == "__main__":
    main()
