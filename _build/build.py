#!/usr/bin/env python3
"""Сборка статей praxor.ru.

Исходники статей лежат в _build/content/<slug>.html: сверху JSON-шапка
между строками <!--meta и -->, ниже тело статьи в HTML.
Форма заявки, подвал и скрипт формы берутся из index.html, чтобы
статьи не расходились с лендингом.

Запуск из корня репозитория:  python3 _build/build.py
GitHub Pages собирает сайт Jekyll-ом, папки с «_» в начале он не публикует.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = Path(__file__).resolve().parent / "content"
SITE = "https://praxor.ru"

MONO = "font-family: 'JetBrains Mono', ui-monospace, monospace;"

landing = (ROOT / "index.html").read_text(encoding="utf-8")


def cut(pattern):
    m = re.search(pattern, landing, re.S)
    if not m:
        raise SystemExit(f"не нашёл в index.html: {pattern}")
    return m.group(0)


HEAD_COMMON = cut(r'<link rel="preconnect" href="https://fonts.googleapis.com" />.*?</noscript>')
LANDING_STYLE = cut(r"<style>.*?</style>")
REQUEST = cut(r'<section id="request".*?</section>')
FOOTER = cut(r"<footer.*?</footer>").replace('href="#request"', 'href="#request"')
FORM_SCRIPT = cut(r"<script>\s*\(function \(\) \{\s*var WEBHOOK.*?</script>")

# Пометка, с какой страницы пришла заявка: landing_version в форме
FORM_SCRIPT = FORM_SCRIPT.replace("var LANDING_VERSION = 'praxxor_v1';",
                                  "var LANDING_VERSION = 'praxxor_v1_article';")

pages = []
for f in sorted(CONTENT.glob("*.html")):
    raw = f.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->\s*(.*)", raw, re.S)
    meta, body = json.loads(m.group(1)), m.group(2)
    meta["slug"] = f.stem
    meta["body"] = body
    pages.append(meta)

by_slug = {p["slug"]: p for p in pages}


def esc(s):
    return html.escape(s, quote=True)


def nav():
    link = f'style="color: #3A4149;"'
    return f"""
  <div style="position: sticky; top: 0; z-index: 60; background: rgba(251,250,248,0.88); backdrop-filter: blur(10px); border-bottom: 1px solid #E2DFDA;">
    <div class="v2-pad" style="max-width: 1280px; margin: 0 auto; padding: 0 40px; display: flex; align-items: center; height: 60px; gap: 40px;">
      <a href="/" style="display: flex; align-items: center; gap: 10px; color: #0E1116;">
        <span style="width: 14px; height: 14px; border: 1.5px solid #0E1116; display: block; position: relative;">
          <span style="position: absolute; left: 3px; top: 3px; width: 5px; height: 5px; background: #1B4DE4; display: block;"></span>
        </span>
        <span style="font-size: 16px; font-weight: 500; letter-spacing: -0.3px;">Праксор</span>
      </a>
      <div class="v2-nav-wide" style="display: flex; align-items: center; gap: 28px; {MONO} font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #3A4149;">
        <a href="/#harness" {link}>Harness</a>
        <a href="/#program" {link}>Программа</a>
        <a href="/#cases" {link}>Кейсы</a>
        <a href="/#team" {link}>Команда</a>
        <a href="/ai-sdlc/" {link}>Материалы</a>
      </div>
      <div class="v2-nav-slim" style="display: flex; align-items: center; gap: 20px; {MONO} font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #3A4149;">
        <a href="/#program" {link}>Программа</a>
        <a href="/ai-sdlc/" {link}>Материалы</a>
      </div>
      <a class="nav-cta" href="#request" style="margin-left: auto; {MONO} font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #0E1116; border: 1px solid #0E1116; padding: 9px 16px; white-space: nowrap;">Оставить заявку</a>
    </div>
  </div>"""


ARTICLE_CSS = """
<style>
  .a-wrap { max-width: 1280px; margin: 0 auto; padding: 0 40px; border-left: 1px solid #E2DFDA; border-right: 1px solid #E2DFDA; }
  .a-crumbs { MONO font-size: 12px; letter-spacing: 0.06em; color: #8B939C; padding-top: 40px; }
  .a-crumbs a { color: #5B646E; }
  .a-crumbs a:hover { color: #1B4DE4; }
  .a-h1 { font-size: 60px; font-weight: 400; line-height: 1.04; letter-spacing: -2px; margin: 40px 0 0; max-width: 20ch; text-wrap: pretty; }
  .a-lead { font-size: 22px; font-weight: 300; line-height: 1.5; letter-spacing: -0.3px; color: #3A4149; margin: 32px 0 0; max-width: 62ch; text-wrap: pretty; }
  .a-meta { MONO font-size: 12px; letter-spacing: 0.06em; color: #8B939C; margin-top: 32px; padding-bottom: 56px; }
  .a-grid { display: grid; grid-template-columns: 3fr 9fr; gap: 56px; border-top: 1px solid #E2DFDA; padding: 56px 0 112px; }
  .a-toc { position: sticky; top: 92px; align-self: start; MONO font-size: 12px; line-height: 1.5; letter-spacing: 0.03em; }
  .a-toc-t { color: #8B939C; text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 14px; }
  .a-toc a { display: block; color: #3A4149; padding: 7px 0; border-top: 1px solid #E2DFDA; }
  .a-toc a:hover { color: #1B4DE4; }
  .a-body { font-size: 18px; line-height: 1.7; color: #1F252C; max-width: 70ch; min-width: 0; overflow-wrap: break-word; }
  .a-body h2 { font-size: 34px; font-weight: 400; line-height: 1.12; letter-spacing: -1px; color: #0E1116; margin: 72px 0 0; scroll-margin-top: 84px; text-wrap: pretty; }
  .a-body h2:first-child { margin-top: 0; }
  .a-body h3 { font-size: 22px; font-weight: 500; line-height: 1.3; letter-spacing: -0.4px; color: #0E1116; margin: 40px 0 0; }
  .a-body p { margin: 18px 0 0; }
  .a-body ul, .a-body ol { margin: 18px 0 0; padding-left: 22px; }
  .a-body li { margin: 8px 0 0; }
  .a-body li::marker { color: #8B939C; }
  .a-body strong { font-weight: 600; color: #0E1116; }
  .a-body a { border-bottom: 1px solid rgba(27,77,228,0.3); }
  .a-body a:hover { border-bottom-color: #0E1116; }
  .a-body code { MONO font-size: 0.86em; background: #F1EFEB; padding: 1px 5px; }
  .a-body pre { MONO font-size: 14px; line-height: 1.6; background: #0E1116; color: #E6E3DD; padding: 24px; margin: 24px 0 0; overflow-x: auto; }
  .a-body pre code { background: none; padding: 0; font-size: inherit; color: inherit; }
  .a-body table { width: 100%; border-collapse: collapse; margin: 24px 0 0; font-size: 16px; line-height: 1.5; }
  .a-body th { MONO font-size: 11px; font-weight: 400; letter-spacing: 0.08em; text-transform: uppercase; color: #8B939C; text-align: left; padding: 0 16px 10px 0; }
  .a-body td { border-top: 1px solid #E2DFDA; padding: 12px 16px 12px 0; vertical-align: top; }
  .a-tbl { overflow-x: auto; }
  .a-note { border-left: 3px solid #1B4DE4; padding: 4px 0 4px 20px; margin: 28px 0 0; color: #3A4149; }
  .a-check { margin: 24px 0 0; border-top: 1px solid #E2DFDA; }
  .a-check label { display: grid; grid-template-columns: 22px 1fr; gap: 14px; padding: 14px 0; border-bottom: 1px solid #E2DFDA; cursor: pointer; font-size: 16px; line-height: 1.55; }
  .a-check input { width: 18px; height: 18px; margin: 4px 0 0; accent-color: #1B4DE4; cursor: pointer; }
  .a-check label:has(input:checked) span { color: #5B646E; }
  .a-check-res { margin: 18px 0 0; padding: 16px 20px; background: #F1EFEB; font-size: 16px; line-height: 1.5; }
  .a-prx { background: #0E1116; color: #FBFAF8; padding: 32px; margin: 48px 0 0; }
  .a-prx h3 { color: #FBFAF8; margin: 0; }
  .a-prx p { color: rgba(251,250,248,0.72); }
  .a-prx a { color: #FBFAF8; border-bottom-color: rgba(251,250,248,0.4); }
  .a-next { margin-top: 72px; border-top: 1px solid #0E1116; padding-top: 24px; }
  .a-next-t { MONO font-size: 12px; letter-spacing: 0.09em; text-transform: uppercase; color: #8B939C; }
  .a-next a { display: block; font-size: 21px; letter-spacing: -0.4px; line-height: 1.35; color: #0E1116; padding: 16px 0; border-top: 1px solid #E2DFDA; border-bottom: none; }
  .a-next a:first-of-type { border-top: none; }
  .a-next a:hover { color: #1B4DE4; }
  .a-next span { display: block; font-size: 15px; color: #5B646E; letter-spacing: 0; margin-top: 4px; }
  .a-faq h3 { margin-top: 28px; }
  .a-body h2#all + .a-next { margin-top: 28px; }
  .a-body h2#all ~ .a-next { margin-top: 40px; }
  @media (max-width: 1000px) {
    .a-wrap { padding-left: 20px; padding-right: 20px; }
    .a-h1 { font-size: 38px; letter-spacing: -1.2px; }
    .a-lead { font-size: 19px; }
    .a-grid { grid-template-columns: 1fr; gap: 0; padding-top: 40px; }
    .a-toc { display: none; }
    .a-body { font-size: 17px; }
    .a-body h2 { font-size: 27px; margin-top: 56px; }
    .a-prx { padding: 24px; }
  }
  @media (max-width: 620px) {
    .a-body table, .a-body tbody, .a-body tr, .a-body td { display: block; width: 100%; }
    .a-body tr:first-child { display: none; }
    .a-body tr { border-top: 1px solid #E2DFDA; padding: 14px 0; }
    .a-body td { border: none; padding: 2px 0; }
    .a-body td:first-child { font-weight: 600; color: #0E1116; }
  }
</style>""".replace("MONO", MONO)


def body_of(p):
    if p["slug"] == "ai-sdlc":
        # каталог встаёт перед блоком вопросов
        return p["body"].replace('<h2 id="faq">', catalog() + '\n\n<h2 id="faq">', 1)
    return p["body"]


def toc(body):
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    links = "\n".join(f'      <a href="#{i}">{re.sub("<[^>]+>", "", t)}</a>' for i, t in items)
    return f'<nav class="a-toc" aria-label="Содержание">\n      <div class="a-toc-t">Содержание</div>\n{links}\n    </nav>'


def related(p):
    links = []
    for s in p.get("related", []):
        r = by_slug[s]
        links.append(f'<a href="/{s}/">{esc(r["h1"])}<span>{esc(r["description"])}</span></a>')
    if not links:
        return ""
    return '<div class="a-next"><div class="a-next-t">Читать дальше</div>' + "".join(links) + "</div>"


# Каталог материалов на странице-хабе /ai-sdlc/
CATALOG = [
    ("Внедрение", ["vnedrenie-ii-v-razrabotku"]),
    ("Подход", ["harness-engineering", "spec-driven-development", "agentic-development",
                "context-engineering", "multi-agent-development"]),
    ("Практики", ["agents-md", "claude-md", "ai-code-review", "ai-test-generation", "llm-gateway"]),
    ("Метрики", ["dora-metrics", "ai-impact-metrics"]),
]


def catalog():
    groups = []
    for title, slugs in CATALOG:
        links = "".join(
            f'<a href="/{s}/">{esc(by_slug[s]["h1"])}<span>{esc(by_slug[s]["description"])}</span></a>'
            for s in slugs if s in by_slug)
        groups.append(f'<div class="a-next"><div class="a-next-t">{title}</div>{links}</div>')
    return '<h2 id="all">Все материалы</h2>\n' + "\n".join(groups)


def ld(p):
    url = f"{SITE}/{p['slug']}/"
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Праксор", "item": f"{SITE}/"}]
    if p["slug"] != "ai-sdlc":
        crumbs.append({"@type": "ListItem", "position": 2, "name": "AI SDLC", "item": f"{SITE}/ai-sdlc/"})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": p["crumb"], "item": url})
    graph = [
        {
            "@type": "Article",
            "@id": url + "#article",
            "headline": p["h1"],
            "description": p["description"],
            "inLanguage": "ru",
            "datePublished": p["published"],
            "dateModified": p.get("modified", p["published"]),
            "mainEntityOfPage": url,
            "author": {"@id": f"{SITE}/#org"},
            "publisher": {"@id": f"{SITE}/#org"},
            "about": p.get("about", []),
        },
        {"@type": "BreadcrumbList", "itemListElement": crumbs},
        {"@type": "ProfessionalService", "@id": f"{SITE}/#org", "name": "Праксор", "url": f"{SITE}/"},
    ]
    faq = re.findall(r'<h3 data-q>(.*?)</h3>\s*<p>(.*?)</p>', p["body"], re.S)
    if faq:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": re.sub("<[^>]+>", "", q),
                 "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a).strip()}}
                for q, a in faq
            ],
        })
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)


def crumbs_html(p):
    parts = ['<a href="/">Праксор</a>']
    if p["slug"] != "ai-sdlc":
        parts.append('<a href="/ai-sdlc/">AI SDLC</a>')
    parts.append(f'<span>{esc(p["crumb"])}</span>')
    return '<nav class="a-crumbs" aria-label="Хлебные крошки">' + " / ".join(parts) + "</nav>"


MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def ru_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def render(p):
    url = f"{SITE}/{p['slug']}/"
    upd = p.get("modified", p["published"])
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(p["title"])}</title>
<meta name="description" content="{esc(p["description"])}" />
<link rel="canonical" href="{url}" />
<meta property="og:title" content="{esc(p["title"])}" />
<meta property="og:description" content="{esc(p["description"])}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{url}" />
<meta property="og:site_name" content="Праксор" />
<meta property="og:locale" content="ru_RU" />
<meta property="og:image" content="{SITE}/og/{p['slug']}.png" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<script type="application/ld+json">
{ld(p)}
</script>
{HEAD_COMMON}
{LANDING_STYLE}
{ARTICLE_CSS}
</head>
<body>
<div style="font-family: 'Geist', -apple-system, system-ui, 'Segoe UI', Helvetica, sans-serif; background: #FBFAF8; color: #0E1116; min-height: 100vh; overflow-x: hidden;">
{nav()}

  <main>
  <div class="a-wrap">
    {crumbs_html(p)}
    <h1 class="a-h1">{esc(p["h1"])}</h1>
    <p class="a-lead">{p["lead"]}</p>
    <div class="a-meta">Обновлено {ru_date(upd)}, {p["read"]} мин чтения</div>
    <div class="a-grid">
    {toc(body_of(p))}
    <article class="a-body">
{body_of(p)}
{"" if p["slug"] == "ai-sdlc" else related(p)}
    </article>
    </div>
  </div>
  </main>

  {REQUEST}

  {FOOTER}
</div>

{FORM_SCRIPT}
</body>
</html>
"""


for p in pages:
    out = ROOT / p["slug"] / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render(p), encoding="utf-8")
    print("собрал", out.relative_to(ROOT))

def render_404():
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Страница не найдена — Праксор</title>
<meta name="robots" content="noindex" />
{HEAD_COMMON}
{LANDING_STYLE}
{ARTICLE_CSS}
</head>
<body>
<div style="font-family: 'Geist', -apple-system, system-ui, 'Segoe UI', Helvetica, sans-serif; background: #FBFAF8; color: #0E1116; min-height: 100vh; overflow-x: hidden;">
{nav()}

  <main>
  <div class="a-wrap">
    <h1 class="a-h1">Такой страницы нет</h1>
    <p class="a-lead">Возможно, в адресе опечатка или страницу перенесли. Начните с <a href="/">главной</a> или выберите материал ниже.</p>
    <article class="a-body" style="max-width: 70ch; margin-top: 48px;">
{catalog()}
    </article>
  </div>
  </main>

  {FOOTER}
</div>
</body>
</html>
"""


(ROOT / "404.html").write_text(render_404().replace('href="#request"', 'href="/#request"'), encoding="utf-8")
print("собрал 404.html")

# sitemap: главная + все статьи
urls = [(f"{SITE}/", "2026-11-12")] + [(f"{SITE}/{p['slug']}/", p.get("modified", p["published"])) for p in pages]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, lm in urls:
    sm += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{lm}</lastmod>", "  </url>"]
sm.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
print("sitemap.xml:", len(urls), "адресов")
