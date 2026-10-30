"""Generate the landing page (docs/index.html) from the live registry.

Counts, categories and the version all come from the code, so the page cannot
claim something the app does not do.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import APP_NAME, APP_TAGLINE, __version__, registry  # noqa: E402

ICON_ACCENT = "#6d8cff"


def category_cards() -> str:
    counts = registry.counts()
    cards = []
    for name in registry.CATEGORY_NAMES:
        blurb = registry.blurb(name)
        cards.append(
            f'      <a class="cat" href="https://github.com/drsamonline/All4ONE/blob/main/TOOL_CATALOG.md">\n'
            f'        <div class="cat-head"><span class="cat-name">{name}</span>'
            f'<span class="cat-count">{counts[name]}</span></div>\n'
            f'        <p>{blurb}</p>\n'
            f'      </a>')
    return "\n".join(cards)


def build() -> str:
    stats = registry.stats()
    tools = stats["tools"]
    ready = stats["ready"]
    stdlib_only = sum(1 for tool in registry.all_tools() if not tool.needs
                      and not tool.is_windows_only)
    categories = stats["categories"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{APP_NAME} — {tools} portable tools, one page each</title>
<meta name="description" content="{APP_NAME} is a portable Windows utility suite: {tools} working tools across {categories} categories, each on its own page, in a single binary. No plugins, no installer, no telemetry.">
<meta name="theme-color" content="#0d1117">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>
<rect width='24' height='24' rx='6' fill='%236d8cff'/><g fill='none' stroke='white' stroke-width='1.6'>
<rect x='5' y='5' width='6' height='6' rx='1.5'/><rect x='13' y='5' width='6' height='6' rx='1.5'/>
<rect x='5' y='13' width='6' height='6' rx='1.5'/><rect x='13' y='13' width='6' height='6' rx='1.5'/>
</g></svg>">
<style>
  :root {{
    --bg: #0d1117; --bg-2: #0a0e14; --surface: #141a22; --surface-2: #1a222c;
    --border: #232d3b; --text: #e6edf3; --dim: #a9b6c6; --muted: #78889b;
    --accent: {ICON_ACCENT}; --accent-2: #4fd1c5; --ok: #3fb950;
    --radius: 16px; --max: 1140px;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: "Segoe UI Variable Text", "Segoe UI", Inter, "Noto Sans", system-ui, sans-serif;
    line-height: 1.6; -webkit-font-smoothing: antialiased;
  }}
  a {{ color: inherit; text-decoration: none; }}
  .wrap {{ max-width: var(--max); margin: 0 auto; padding: 0 24px; }}
  .glow {{
    position: absolute; inset: -20% 20% auto; height: 620px; pointer-events: none;
    background: radial-gradient(circle at 50% 0%, rgba(109,140,255,.28), transparent 62%);
    filter: blur(20px);
  }}
  header {{ position: relative; overflow: hidden; padding: 30px 0 10px; }}
  nav {{
    display: flex; align-items: center; gap: 18px; padding: 6px 0 34px;
  }}
  .brand {{ display: flex; align-items: center; gap: 11px; font-weight: 700; font-size: 17px; }}
  .mark {{
    width: 34px; height: 34px; border-radius: 10px; background: var(--accent);
    display: grid; place-items: center;
  }}
  .mark svg {{ width: 20px; height: 20px; }}
  nav .links {{ margin-left: auto; display: flex; gap: 22px; color: var(--dim); font-size: 14px; }}
  nav .links a:hover {{ color: var(--text); }}
  @media (max-width: 720px) {{ nav .links {{ display: none; }} }}

  .hero {{ position: relative; text-align: center; padding: 26px 0 60px; }}
  h1 {{
    font-size: clamp(34px, 6vw, 60px); line-height: 1.06; margin: 0 0 18px;
    letter-spacing: -0.03em; font-weight: 800;
  }}
  h1 em {{
    font-style: normal;
    background: linear-gradient(100deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }}
  .lede {{ font-size: clamp(15px, 2vw, 18px); color: var(--dim); max-width: 720px; margin: 0 auto 26px; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 9px; justify-content: center; margin-bottom: 30px; }}
  .pill {{
    font-size: 13px; padding: 6px 13px; border-radius: 999px;
    border: 1px solid var(--border); background: var(--surface); color: var(--dim);
  }}
  .pill b {{ color: var(--text); }}
  .pill.ok {{ border-color: rgba(63,185,80,.4); color: #9be3a8; }}
  .cta {{ display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 9px; padding: 13px 22px;
    border-radius: 12px; font-weight: 600; font-size: 15px; border: 1px solid var(--border);
    background: var(--surface-2); transition: .16s ease;
  }}
  .btn:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
  .btn.primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
  .btn.primary:hover {{ background: #7f9bff; }}
  .btn svg {{ width: 17px; height: 17px; }}

  .shot {{
    margin: 56px auto 0; max-width: 1020px; border-radius: var(--radius);
    border: 1px solid var(--border); background: var(--surface);
    padding: 10px; box-shadow: 0 30px 80px -30px rgba(0,0,0,.9);
  }}
  .shot img {{ width: 100%; display: block; border-radius: 10px; }}
  .shot figcaption {{ color: var(--muted); font-size: 13px; text-align: center; padding: 10px 0 2px; }}

  section {{ padding: 74px 0; border-top: 1px solid var(--border); }}
  h2 {{ font-size: clamp(24px, 3.4vw, 34px); letter-spacing: -0.02em; margin: 0 0 12px; }}
  .sub {{ color: var(--dim); max-width: 660px; margin: 0 0 34px; }}
  .grid {{ display: grid; gap: 16px; }}
  .g3 {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
  .g2 {{ grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); }}
  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 22px;
  }}
  .card h3 {{ margin: 0 0 8px; font-size: 16px; }}
  .card p {{ margin: 0; color: var(--dim); font-size: 14.5px; }}
  .card .ico {{
    width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center;
    background: rgba(109,140,255,.14); margin-bottom: 14px;
  }}
  .card .ico svg {{ width: 19px; height: 19px; stroke: var(--accent); fill: none; stroke-width: 1.8; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 14.5px; }}
  th, td {{ text-align: left; padding: 11px 14px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: .06em; }}
  td:first-child {{ color: var(--muted); width: 34%; }}
  tr:last-child td {{ border-bottom: none; }}

  .cats {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
  .cat {{
    display: block; background: var(--surface); border: 1px solid var(--border);
    border-radius: 13px; padding: 16px; transition: .16s ease;
  }}
  .cat:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
  .cat-head {{ display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }}
  .cat-name {{ font-weight: 650; font-size: 14.5px; }}
  .cat-count {{
    margin-left: auto; font-size: 12px; color: var(--accent);
    background: rgba(109,140,255,.12); padding: 1px 8px; border-radius: 999px;
  }}
  .cat p {{ margin: 0; color: var(--muted); font-size: 13px; }}

  pre {{
    background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 20px; overflow-x: auto; font-size: 13.5px; line-height: 1.75;
    font-family: "Cascadia Mono", Consolas, "DejaVu Sans Mono", monospace;
    color: #c9d6e4;
  }}
  pre .c {{ color: var(--muted); }}
  pre .k {{ color: var(--accent); }}
  pre .s {{ color: var(--accent-2); }}

  footer {{ padding: 46px 0 60px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--border); }}
  footer .row {{ display: flex; flex-wrap: wrap; gap: 18px; align-items: center; }}
  footer a {{ color: var(--dim); }}
  footer a:hover {{ color: var(--text); }}
  .spacer {{ margin-left: auto; }}
</style>
</head>
<body>
<div class="glow"></div>

<header class="wrap">
  <nav>
    <div class="brand">
      <span class="mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7" stroke-linejoin="round">
          <rect x="4" y="4" width="7" height="7" rx="1.6"/><rect x="13" y="4" width="7" height="7" rx="1.6"/>
          <rect x="4" y="13" width="7" height="7" rx="1.6"/><rect x="13" y="13" width="7" height="7" rx="1.6"/>
        </svg>
      </span>
      {APP_NAME}
    </div>
    <div class="links">
      <a href="#tools">Tools</a>
      <a href="#inside">Inside</a>
      <a href="#cli">Command line</a>
      <a href="https://github.com/drsamonline/All4ONE/blob/main/USER_GUIDE.md">Guide</a>
      <a href="https://github.com/drsamonline/All4ONE">GitHub</a>
    </div>
  </nav>

  <div class="hero">
    <h1>{tools} tools.<br><em>One page each.</em></h1>
    <p class="lede">
      {APP_TAGLINE} A portable Windows utility suite that does file work, text, data,
      images, PDFs, media, documents, networking, system maintenance, security and
      calculations — in one binary with nothing to install and nothing running in the
      background.
    </p>
    <div class="pills">
      <span class="pill"><b>{tools}</b> tools</span>
      <span class="pill"><b>{categories}</b> categories</span>
      <span class="pill ok"><b>0</b> plugins</span>
      <span class="pill"><b>{stdlib_only}</b> need no extra software</span>
      <span class="pill"><b>v{__version__}</b></span>
    </div>
    <div class="cta">
      <a class="btn primary" href="https://github.com/drsamonline/All4ONE/releases/latest">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
             stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 11l5 5 5-5"/>
             <path d="M4 20h16"/></svg>
        Download for Windows
      </a>
      <a class="btn" href="https://github.com/drsamonline/All4ONE/blob/main/TOOL_CATALOG.md">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
             stroke-linecap="round"><path d="M5 6h14M5 12h14M5 18h9"/></svg>
        Browse all {tools} tools
      </a>
    </div>

    <figure class="shot">
      <img src="screenshots/home-dark.png" alt="All4one home page: search, tool counters and category grid" loading="lazy">
      <figcaption>Home — search, favourites, recents and every category. Dark theme shown; light is one click away.</figcaption>
    </figure>
  </div>
</header>

<section id="inside">
  <div class="wrap">
    <h2>Built the way the last one should have been</h2>
    <p class="sub">
      Version 4 is a rewrite, not a reskin. The plugin packs, the single dense table
      and the free-text argument box are gone. What replaced them is a tool contract
      that generates the interface, the CLI and the catalogue from one declaration.
    </p>
    <table>
      <tr><th>Before (3.x)</th><th>Now (4.0)</th></tr>
      <tr><td>45 plugin packs, a Packs tab, enable/disable toggles</td><td>One flat catalogue — nothing to enable, nothing to install</td></tr>
      <tr><td>551 tools, many trivial or duplicated</td><td>{tools} tools, each with a real implementation and its own options</td></tr>
      <tr><td>One table for everything, free-text arguments</td><td>A page per tool, with typed controls generated from its schema</td></tr>
      <tr><td>Output appeared when the run finished</td><td>Streamed output, progress, and a stop button</td></tr>
      <tr><td>Registry smoke test only</td><td>Every runnable tool executed against fixtures on every build</td></tr>
    </table>

    <div class="grid g3" style="margin-top:34px">
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/>
          <path d="M3 9h18M9 9v11"/></svg></div>
        <h3>One page per tool</h3>
        <p>Every tool opens its own page: its name, what it does, its options, and its
           output. No hunting through a grid of 500 rows to find the argument order.</p>
      </div>
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h10M4 17h13"/>
          <circle cx="18" cy="12" r="2"/></svg></div>
        <h3>Options that fit the tool</h3>
        <p>Dropdowns for algorithms, sliders for quality, colour pickers, toggles, and
           file pickers that accept a dropped file. Required options are marked.</p>
      </div>
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><path d="M5 5h14v14H5z"/><path d="M8 10h8M8 14h5"/></svg></div>
        <h3>Live output</h3>
        <p>Lines appear as the tool works. Long jobs show a progress bar and can be
           stopped. Results can be copied, saved, or opened straight from the page.</p>
      </div>
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v9"/></svg></div>
        <h3>One binary, no installer</h3>
        <p>Run it from a folder or a USB stick. No registry entries, no services, no
           background processes, no telemetry — and one small settings file.</p>
      </div>
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><path d="M12 3v6M12 15v6M5 12H3M21 12h-2"/>
          <circle cx="12" cy="12" r="4"/></svg></div>
        <h3>Missing extras never break it</h3>
        <p>FFmpeg, Tesseract, Pillow and friends are optional. A tool that needs one
           still appears, says exactly what to install, and the rest of the app is
           untouched.</p>
      </div>
      <div class="card">
        <div class="ico"><svg viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg></div>
        <h3>A catalogue that is checked</h3>
        <p>The build runs every tool against generated test files before it packages
           anything. A tool that stops working fails the build rather than shipping.</p>
      </div>
    </div>
  </div>
</section>

<section id="tools">
  <div class="wrap">
    <h2>{categories} categories, {tools} tools</h2>
    <p class="sub">Grouped by what you are trying to do, not by how the code is organised.</p>
    <div class="cats">
{category_cards()}
    </div>
    <p class="sub" style="margin:30px 0 0">
      <a class="btn" href="https://github.com/drsamonline/All4ONE/blob/main/TOOL_CATALOG.md">
        Open the full catalogue — every tool, every option</a>
    </p>
  </div>
</section>

<section id="cli">
  <div class="wrap">
    <h2>The same binary is a command line</h2>
    <p class="sub">
      Every option on a tool page has an identical flag, generated from the same
      schema — so a job you set up in the window can be pasted straight into a script.
    </p>
    <pre><span class="c"># every tool, grouped by category</span>
all4one <span class="k">list</span>

<span class="c"># what does this tool take?</span>
all4one <span class="k">show</span> pdf-extract-pages

<span class="c"># run it</span>
all4one <span class="k">run</span> pdf-extract-pages <span class="s">--file</span> book.pdf <span class="s">--pages</span> "1-3,7" <span class="s">--output</span> ch1.pdf
all4one <span class="k">run</span> hash-file <span class="s">--file</span> release.zip <span class="s">--algorithm</span> sha256
all4one <span class="k">run</span> bulk-rename <span class="s">--folder</span> C:\\photos <span class="s">--find</span> IMG <span class="s">--replace</span> holiday <span class="s">--apply</span>
all4one <span class="k">run</span> gst-calc <span class="s">--amount</span> 10000 <span class="s">--rate</span> 18

<span class="c"># what optional extras are installed?</span>
all4one <span class="k">deps</span></pre>
  </div>
</section>

<section>
  <div class="wrap">
    <h2>Inside</h2>
    <div class="grid g2">
      <figure class="shot" style="margin:0; max-width:none">
        <img src="screenshots/tool-page.png" alt="A tool page: options on the left, output console on the right" loading="lazy">
        <figcaption>A tool page — options on the left, streamed output on the right.</figcaption>
      </figure>
      <figure class="shot" style="margin:0; max-width:none">
        <img src="screenshots/category.png" alt="A category listing of tool cards" loading="lazy">
        <figcaption>Category view — each card shows what the tool does and what it needs.</figcaption>
      </figure>
    </div>
    <div class="grid g2" style="margin-top:16px">
      <figure class="shot" style="margin:0; max-width:none">
        <img src="screenshots/home-light.png" alt="All4one in the light theme" loading="lazy">
        <figcaption>Light theme.</figcaption>
      </figure>
      <figure class="shot" style="margin:0; max-width:none">
        <img src="screenshots/dependencies.png" alt="The dependencies page listing optional components" loading="lazy">
        <figcaption>Dependencies — what each optional component unlocks, and how to get it.</figcaption>
      </figure>
    </div>
  </div>
</section>

<footer>
  <div class="wrap row">
    <span>© 2026 Dr. Sohil Momin · PolyForm Noncommercial 1.0.0</span>
    <span class="spacer"></span>
    <a href="https://github.com/drsamonline/All4ONE">Source</a>
    <a href="https://github.com/drsamonline/All4ONE/blob/main/USER_GUIDE.md">User guide</a>
    <a href="https://github.com/drsamonline/All4ONE/blob/main/INSTALLATION.md">Install</a>
    <a href="https://github.com/drsamonline/All4ONE/blob/main/DEVELOPER_GUIDE.md">Develop</a>
    <a href="https://drsamonline.github.io/">All projects</a>
  </div>
</footer>
</body>
</html>
"""


def main() -> int:
    target = ROOT / "docs" / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build(), encoding="utf-8")
    stats = registry.stats()
    print(f"wrote {target} ({stats['tools']} tools, {stats['categories']} categories)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
