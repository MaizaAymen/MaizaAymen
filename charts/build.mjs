// Renders Recharts charts to static SVG (dark + light) for the profile README.
// GitHub can't run JS, so the charts are server-rendered once and committed;
// the daily workflow re-runs this to keep the numbers current.
//   cd charts && npm ci && node build.mjs
import { writeFileSync } from "node:fs";
import { createElement as h } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  Bar, BarChart, CartesianGrid, LabelList, ReferenceLine, XAxis, YAxis,
} from "recharts";

const USER = "MaizaAymen";
const OUT = new URL("../assets/", import.meta.url);
const FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif";

const THEMES = {
  dark: { surface: "#0d1117", border: "#30363d", grid: "#21262d", axis: "#30363d",
          ink: "#e6edf3", ink2: "#8b949e", series: "#58a6ff", accent: "#3fb950" },
  light: { surface: "#ffffff", border: "#d0d7de", grid: "#eaeef2", axis: "#d0d7de",
           ink: "#1f2328", ink2: "#59636e", series: "#0969da", accent: "#1a7f37" },
};

// ── data ────────────────────────────────────────────────────────────────
async function api(path) {
  const headers = { "User-Agent": USER, Accept: "application/vnd.github+json" };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(`https://api.github.com${path}`, { headers });
      if (!res.ok) throw new Error(`${res.status} ${path}`);
      return await res.json();
    } catch (err) {
      if (attempt === 2) throw err;
      await new Promise((r) => setTimeout(r, 2000));
    }
  }
}

async function collect() {
  let repos = [];
  for (let page = 1; ; page++) {
    const batch = await api(`/users/${USER}/repos?per_page=100&page=${page}`);
    repos = repos.concat(batch);
    if (batch.length < 100) break;
  }
  // the profile repo itself isn't a project
  const own = repos.filter((r) => !r.fork && r.name !== USER);

  // projects started per quarter, with empty quarters kept so gaps stay honest
  const q = (d) => `${d.getUTCFullYear()} Q${Math.floor(d.getUTCMonth() / 3) + 1}`;
  const dates = own.map((r) => new Date(r.created_at)).sort((a, b) => a - b);
  const counts = new Map();
  for (let d = new Date(Date.UTC(dates[0].getUTCFullYear(), Math.floor(dates[0].getUTCMonth() / 3) * 3, 1));
       d <= new Date(); d.setUTCMonth(d.getUTCMonth() + 3)) counts.set(q(d), 0);
  for (const d of dates) counts.set(q(d), counts.get(q(d)) + 1);
  const quarters = [...counts].map(([quarter, n]) => ({ quarter, n }));

  // primary language per original repo (repos with no detected language are left out)
  const langCount = new Map();
  for (const r of own) if (r.language) langCount.set(r.language, (langCount.get(r.language) ?? 0) + 1);
  const langs = [...langCount].map(([lang, n]) => ({ lang, n })).sort((a, b) => b.n - a.n).slice(0, 7);

  return { quarters, langs, total: own.length, withLang: [...langCount.values()].reduce((a, b) => a + b, 0) };
}

// ── chart frame ─────────────────────────────────────────────────────────
// Recharts emits <svg class="recharts-surface">; we wrap it in a card with a title.
function frame(t, { width, height, title, subtitle, chart, footnote }) {
  const inner = renderToStaticMarkup(chart).match(/<svg[\s\S]*<\/svg>/)[0]
    .replace("<svg", `<svg x="0" y="76"`);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" font-family="${FONT}">
<rect x=".5" y=".5" width="${width - 1}" height="${height - 1}" rx="14" fill="${t.surface}" stroke="${t.border}"/>
<text x="28" y="40" font-size="18" font-weight="700" fill="${t.ink}">${title}</text>
<text x="28" y="62" font-size="13" fill="${t.ink2}">${subtitle}</text>
${inner}
<text x="28" y="${height - 16}" font-size="11" fill="${t.ink2}">${footnote}</text>
</svg>`;
}

const tick = (t) => ({ fill: t.ink2, fontSize: 12, fontFamily: FONT });

// ── 1. projects started per quarter (column chart, single series) ───────
function cadence(t, data) {
  const max = Math.max(...data.map((d) => d.n));
  const peak = data.find((d) => d.n === max).quarter;
  const avg = data.reduce((s, d) => s + d.n, 0) / data.length;
  // clean tick steps: 0 / 10 / 20 / 30 rather than Recharts' 0 / 7 / 14 ...
  const step = max > 20 ? 10 : 5;
  const top = Math.ceil(max / step) * step;
  const ticks = Array.from({ length: top / step + 1 }, (_, i) => i * step);
  const width = 580, height = 360;
  const chart = h(BarChart, { width, height: height - 110, data, margin: { top: 22, right: 28, bottom: 8, left: 4 } },
    h(CartesianGrid, { vertical: false, stroke: t.grid, strokeWidth: 1 }),
    h(XAxis, { dataKey: "quarter", tick: tick(t), tickLine: false, axisLine: { stroke: t.axis },
               interval: 0, tickFormatter: (v) => v.replace(" ", " ").replace(/^20(\d\d) /, "’$1 "), height: 24 }),
    h(YAxis, { tick: tick(t), tickLine: false, axisLine: false, width: 34, domain: [0, top], ticks }),
    h(ReferenceLine, { y: avg, stroke: t.ink2, strokeDasharray: "3 4", strokeWidth: 1,
                       label: { value: `avg ${avg.toFixed(1)}`, position: "insideTopRight", fill: t.ink2, fontSize: 11 } }),
    h(Bar, { dataKey: "n", fill: t.series, radius: [4, 4, 0, 0], maxBarSize: 24, isAnimationActive: false },
      // label only the peak — the axis carries the rest
      h(LabelList, { dataKey: "n", position: "top", fill: t.ink, fontSize: 12, fontWeight: 700,
                     formatter: (v) => (v === max ? v : "") })));
  return frame(t, {
    width, height, chart,
    title: "Shipping cadence",
    subtitle: `New original repositories per quarter · peak ${max} in ${peak}`,
    footnote: `Source: GitHub API, ${data.reduce((s, d) => s + d.n, 0)} original repos (forks excluded) · auto-updated daily`,
  });
}

// ── 2. languages across original repos (horizontal bars, single series) ─
function languages(t, data, withLang) {
  const width = 580, height = 360;
  const chart = h(BarChart, { width, height: height - 110, data, layout: "vertical",
                              margin: { top: 8, right: 64, bottom: 8, left: 8 }, barCategoryGap: 6 },
    h(CartesianGrid, { horizontal: false, stroke: t.grid, strokeWidth: 1 }),
    h(XAxis, { type: "number", tick: tick(t), tickLine: false, axisLine: false, allowDecimals: false }),
    h(YAxis, { type: "category", dataKey: "lang", tick: { ...tick(t), fill: t.ink, fontSize: 13 },
               tickLine: false, axisLine: { stroke: t.axis }, width: 92 }),
    h(Bar, { dataKey: "n", fill: t.series, radius: [0, 4, 4, 0], maxBarSize: 22, isAnimationActive: false },
      h(LabelList, { dataKey: "n", position: "right", fill: t.ink2, fontSize: 12,
                     formatter: (v) => `${v} · ${Math.round((v / withLang) * 100)}%` })));
  return frame(t, {
    width, height, chart,
    title: "What I build in",
    subtitle: `Primary language of each original repository (top ${data.length})`,
    footnote: `Source: GitHub API, ${withLang} repos with a detected language · auto-updated daily`,
  });
}

const d = await collect();
for (const [name, t] of Object.entries(THEMES)) {
  writeFileSync(new URL(`chart-cadence-${name}.svg`, OUT), cadence(t, d.quarters));
  writeFileSync(new URL(`chart-languages-${name}.svg`, OUT), languages(t, d.langs, d.withLang));
}
console.log(`ok: ${d.total} repos, ${d.quarters.length} quarters, langs`, d.langs.map((l) => `${l.lang}:${l.n}`).join(" "));
