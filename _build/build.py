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
      <a href="/" aria-label="Праксор — на главную" style="display: flex; align-items: center; color: #0E1116;">
        <svg viewBox="0 -12.68 90.15 15.08" width="90.15" height="15.08" role="img" aria-label="Праксор" style="display: block;"><g transform="translate(0 -12.68)"><rect x="0.75" y="0.75" width="12.5" height="12.5" fill="none" stroke="#0E1116" stroke-width="1.5"/><rect x="4.5" y="4.5" width="5" height="5" fill="#1B4DE4"/></g><path d="M1.38 0L1.38 -11.36L10.08 -11.36L10.08 0L8.35 0L8.35 -9.78L3.1 -9.78L3.1 0L1.38 0ZM12.36 2.4L12.36 -8.51L13.96 -8.51L14 -6.69L13.81 -6.78Q14.13 -7.73 14.87 -8.22Q15.6 -8.7 16.56 -8.7Q17.81 -8.7 18.62 -8.09Q19.43 -7.47 19.82 -6.46Q20.21 -5.46 20.21 -4.26Q20.21 -3.06 19.82 -2.05Q19.43 -1.04 18.62 -0.42Q17.81 0.19 16.56 0.19Q15.92 0.19 15.36 -0.03Q14.8 -0.26 14.41 -0.66Q14.02 -1.07 13.86 -1.63L14.05 -1.82L14.05 2.4L12.36 2.4ZM16.26 -1.28Q17.28 -1.28 17.87 -2.06Q18.45 -2.85 18.45 -4.26Q18.45 -5.66 17.87 -6.45Q17.28 -7.23 16.26 -7.23Q15.59 -7.23 15.09 -6.9Q14.6 -6.58 14.32 -5.9Q14.05 -5.23 14.05 -4.26Q14.05 -3.28 14.32 -2.61Q14.58 -1.94 15.08 -1.61Q15.59 -1.28 16.26 -1.28ZM24.17 0.19Q22.84 0.19 22.05 -0.42Q21.26 -1.02 21.26 -2.13Q21.26 -3.23 21.92 -3.85Q22.58 -4.46 23.98 -4.74L26.9 -5.3Q26.9 -6.29 26.44 -6.78Q25.98 -7.26 25.06 -7.26Q24.25 -7.26 23.78 -6.9Q23.32 -6.54 23.14 -5.84L21.4 -5.95Q21.64 -7.23 22.59 -7.97Q23.54 -8.7 25.06 -8.7Q26.79 -8.7 27.7 -7.78Q28.6 -6.86 28.6 -5.2L28.6 -1.89Q28.6 -1.58 28.7 -1.46Q28.81 -1.34 29.05 -1.34L29.35 -1.34L29.35 0Q29.27 0.02 29.1 0.03Q28.92 0.05 28.73 0.05Q28.18 0.05 27.79 -0.13Q27.4 -0.3 27.21 -0.71Q27.02 -1.12 27.02 -1.81L27.19 -1.73Q27.06 -1.17 26.64 -0.74Q26.22 -0.3 25.57 -0.06Q24.92 0.19 24.17 0.19ZM24.44 -1.15Q25.21 -1.15 25.75 -1.45Q26.3 -1.74 26.6 -2.27Q26.9 -2.8 26.9 -3.47L26.9 -4.02L24.41 -3.54Q23.64 -3.39 23.33 -3.08Q23.02 -2.77 23.02 -2.29Q23.02 -1.74 23.39 -1.45Q23.77 -1.15 24.44 -1.15ZM36.09 0L32.04 -4.24L35.93 -8.51L38.01 -8.51L33.98 -4.26L38.17 0L36.09 0ZM30.52 0L30.52 -8.51L32.22 -8.51L32.22 0L30.52 0ZM43.31 0.19Q42.1 0.19 41.18 -0.35Q40.27 -0.9 39.78 -1.9Q39.28 -2.91 39.28 -4.26Q39.28 -5.6 39.78 -6.6Q40.27 -7.6 41.18 -8.15Q42.1 -8.7 43.31 -8.7Q44.35 -8.7 45.16 -8.34Q45.97 -7.98 46.47 -7.3Q46.98 -6.61 47.12 -5.62L45.34 -5.52Q45.22 -6.35 44.67 -6.79Q44.13 -7.23 43.31 -7.23Q42.24 -7.23 41.64 -6.44Q41.04 -5.65 41.04 -4.26Q41.04 -2.86 41.64 -2.07Q42.24 -1.28 43.31 -1.28Q44.13 -1.28 44.67 -1.74Q45.22 -2.19 45.34 -3.12L47.12 -3.02Q46.98 -2.05 46.47 -1.33Q45.97 -0.61 45.16 -0.21Q44.35 0.19 43.31 0.19ZM52.02 0.19Q50.8 0.19 49.89 -0.35Q48.98 -0.9 48.48 -1.9Q47.99 -2.91 47.99 -4.26Q47.99 -5.62 48.48 -6.61Q48.98 -7.6 49.89 -8.15Q50.8 -8.7 52.02 -8.7Q53.24 -8.7 54.15 -8.15Q55.06 -7.6 55.56 -6.61Q56.05 -5.62 56.05 -4.26Q56.05 -2.91 55.56 -1.9Q55.06 -0.9 54.15 -0.35Q53.24 0.19 52.02 0.19ZM52.02 -1.28Q53.11 -1.28 53.7 -2.07Q54.29 -2.86 54.29 -4.26Q54.29 -5.65 53.7 -6.44Q53.11 -7.23 52.02 -7.23Q50.95 -7.23 50.35 -6.44Q49.75 -5.65 49.75 -4.26Q49.75 -2.86 50.35 -2.07Q50.95 -1.28 52.02 -1.28ZM57.62 2.4L57.62 -8.51L59.22 -8.51L59.27 -6.69L59.08 -6.78Q59.4 -7.73 60.14 -8.22Q60.87 -8.7 61.83 -8.7Q63.08 -8.7 63.89 -8.09Q64.7 -7.47 65.09 -6.46Q65.48 -5.46 65.48 -4.26Q65.48 -3.06 65.09 -2.05Q64.7 -1.04 63.89 -0.42Q63.08 0.19 61.83 0.19Q61.19 0.19 60.63 -0.03Q60.07 -0.26 59.68 -0.66Q59.29 -1.07 59.13 -1.63L59.32 -1.82L59.32 2.4L57.62 2.4ZM61.53 -1.28Q62.55 -1.28 63.14 -2.06Q63.72 -2.85 63.72 -4.26Q63.72 -5.66 63.14 -6.45Q62.55 -7.23 61.53 -7.23Q60.86 -7.23 60.36 -6.9Q59.86 -6.58 59.59 -5.9Q59.32 -5.23 59.32 -4.26Q59.32 -3.28 59.58 -2.61Q59.85 -1.94 60.35 -1.61Q60.86 -1.28 61.53 -1.28Z" transform="translate(24 0)" fill="#0E1116"/></svg>
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
  .a-copy { display: block; margin: 24px 0 0 auto; MONO font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #0E1116; background: transparent; border: 1px solid #0E1116; padding: 8px 14px; cursor: pointer; }
  .a-copy:hover { background: #0E1116; color: #FBFAF8; }
  .a-copy + pre { margin-top: 8px; }
  .a-body pre[data-copy] { white-space: pre-wrap; overflow-wrap: anywhere; }
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
    ("Внедрение", ["vnedrenie-ii-v-razrabotku", "ai-pilot-templates"]),
    ("Подход", ["harness-engineering", "spec-driven-development", "agentic-development",
                "context-engineering", "multi-agent-development"]),
    ("Практики", ["agents-md", "agents-md-templates", "claude-md", "ai-code-review", "ai-test-generation", "llm-gateway"]),
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
<meta property="article:published_time" content="{p["published"]}" />
<meta property="article:modified_time" content="{upd}" />
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


# llms.txt: карта сайта для языковых моделей (формат llmstxt.org)
def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)

llms = [
    "# Праксор",
    "",
    "> Праксор выстраивает AI SDLC в инженерных командах: за 3 месяца внедряет AI-агентов в процесс разработки на пилотной команде и измеряет эффект DORA-метриками и AI-метриками против стартового замера.",
    "",
    "Сайт на русском языке. Основатели: Асхат Уразбаев, Кирилл Мокевнин, Алексей Могильников, Сергей Липчанский. Связаться: hello@praxor.ru.",
    "",
    "## Компания",
    "",
    f"- [Праксор]({SITE}/): программа пилота из пяти шагов, уровни зрелости AI SDLC, слои harness, кейсы, команда",
    f"- [AI SDLC]({SITE}/ai-sdlc/): {by_slug['ai-sdlc']['description']}",
]
for title, slugs in CATALOG:
    llms += ["", f"## {title}", ""]
    for s in slugs:
        q = by_slug[s]
        llms.append(f"- [{strip_tags(q['h1'])}]({SITE}/{s}/): {q['description']}")
(ROOT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
print("llms.txt:", sum(1 for l in llms if l.startswith("- [")), "ссылок")

# Atom-лента материалов
def xesc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

feed_pages = sorted(pages, key=lambda q: (q.get("modified", q["published"]), q["slug"]), reverse=True)
feed_upd = feed_pages[0].get("modified", feed_pages[0]["published"])
feed = ['<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="ru">',
        '  <title>Праксор — материалы об AI SDLC</title>',
        '  <subtitle>Практические руководства по внедрению AI-агентов в разработку</subtitle>',
        f'  <link href="{SITE}/feed.xml" rel="self" />',
        f'  <link href="{SITE}/ai-sdlc/" />',
        f'  <id>{SITE}/feed.xml</id>',
        f'  <updated>{feed_upd}T00:00:00Z</updated>',
        '  <author><name>Праксор</name><email>hello@praxor.ru</email></author>']
for q in feed_pages:
    url = f"{SITE}/{q['slug']}/"
    feed += ['  <entry>',
             f'    <title>{xesc(strip_tags(q["h1"]))}</title>',
             f'    <link href="{url}" />',
             f'    <id>{url}</id>',
             f'    <published>{q["published"]}T00:00:00Z</published>',
             f'    <updated>{q.get("modified", q["published"])}T00:00:00Z</updated>',
             f'    <summary>{xesc(q["description"])}</summary>',
             '  </entry>']
feed.append('</feed>')
(ROOT / "feed.xml").write_text("\n".join(feed) + "\n", encoding="utf-8")
print("feed.xml:", len(feed_pages), "записей")

# sitemap: главная + все статьи
urls = [(f"{SITE}/", "2026-11-12")] + [(f"{SITE}/{p['slug']}/", p.get("modified", p["published"])) for p in pages]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, lm in urls:
    sm += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{lm}</lastmod>", "  </url>"]
sm.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
print("sitemap.xml:", len(urls), "адресов")
