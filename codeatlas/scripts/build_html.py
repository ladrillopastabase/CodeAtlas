#!/usr/bin/env python3
"""Build the navigable HTML version of the manuals (phase 7).

Usage:
    python build_html.py manual-docs [--title "Name"] [--out manual-docs/html]
                         [--language en]

Turns each manual-docs/manuals/*.md into a self-contained HTML page (styles
inlined) with:
  - a sidebar listing the documents and the page's table of contents
  - > [!WARNING], [!NOTE], [!IMPORTANT], [!TIP], [!TO VERIFY] and
    [!SCREENSHOT PENDING] callouts rendered as boxes (Spanish aliases such as
    [!ADVERTENCIA] or [!POR VERIFICAR] also work)
  - heading anchors, .md links rewritten to .html, scrollable tables
  - automatic dark mode and print styles (for exporting to PDF)
  - previous / next navigation

index.html comes from 00-index.md when it exists; otherwise a cover page with
a card per document is created. Screenshots in manual-docs/screenshots are
copied to html/screenshots. Interface labels (sidebar, callout titles) follow
the language in state.json (en or es) unless --language is given.

Uses the 'markdown' package when installed; otherwise a built-in converter
that covers headings, paragraphs, nested lists, tables, code, quotes, links
and images.
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path
from string import Template

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import CALLOUTS, list_manuals, setup_output, slug  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent

LABELS = {
    "en": {
        "note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning",
        "verify": "To verify", "screenshot": "Screenshot pending",
        "documents": "Documents", "on_this_page": "On this page", "home": "Home",
        "menu": "Contents", "skip": "Skip to content", "nav": "Manual navigation",
        "generated": "Generated from the application's source code on",
        "version": "Documented version", "prev_next": "Previous and next document",
        "cover_intro": "User documentation. Pick the document that matches your role or task.",
        "anchor": "Link to this section",
    },
    "es": {
        "note": "Nota", "tip": "Consejo", "important": "Importante", "warning": "Advertencia",
        "verify": "Por verificar", "screenshot": "Captura pendiente",
        "documents": "Documentos", "on_this_page": "En esta página", "home": "Inicio",
        "menu": "Contenido", "skip": "Ir al contenido", "nav": "Navegación del manual",
        "generated": "Generado a partir del código fuente de la aplicación el",
        "version": "Versión documentada", "prev_next": "Documento anterior y siguiente",
        "cover_intro": "Documentación de usuario. Seleccione el documento que corresponde a su perfil o tarea.",
        "anchor": "Enlace a esta sección",
    },
}

# ------------------------------------------------------------------ converter

try:
    import markdown as _md  # type: ignore

    def md_to_html(text):
        return _md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"], output_format="html5")

    ENGINE = "markdown " + getattr(_md, "__version__", "")
except Exception:  # pragma: no cover - depends on the environment
    _md = None
    ENGINE = "built-in converter"

    def _inline(t):
        codes = []

        def keep_code(m):
            codes.append("<code>" + html.escape(m.group(1)) + "</code>")
            return f"\x00{len(codes) - 1}\x00"

        t = re.sub(r"`([^`]+)`", keep_code, t)
        comments = []

        def keep_comment(m):
            comments.append(m.group(0))
            return f"\x01{len(comments) - 1}\x01"

        t = re.sub(r"<!--.*?-->", keep_comment, t)
        t = html.escape(t, quote=False)
        t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', t)
        t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
        t = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", t)
        t = re.sub(r"  $", "<br>", t, flags=re.M)
        t = re.sub(r"\x01(\d+)\x01", lambda m: comments[int(m.group(1))], t)
        return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t)

    def _cells(line):
        line = line.strip().strip("|")
        return [c.strip() for c in re.split(r"(?<!\\)\|", line)]

    def md_to_html(text):  # noqa: C901
        lines = text.split("\n")
        out, i, n = [], 0, len(lines)
        is_item = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)")
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            m = re.match(r"^\s*(```|~~~)(\w*)", line)
            if m:
                fence = m.group(1)
                i += 1
                buf = []
                while i < n and not lines[i].strip().startswith(fence):
                    buf.append(lines[i])
                    i += 1
                i += 1
                out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
                continue
            m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
            if m:
                k = len(m.group(1))
                out.append(f"<h{k}>{_inline(m.group(2))}</h{k}>")
                i += 1
                continue
            if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
                out.append("<hr>")
                i += 1
                continue
            if line.lstrip().startswith("<"):
                buf = []
                while i < n and lines[i].strip():
                    buf.append(lines[i])
                    i += 1
                out.append("\n".join(buf))
                continue
            if "|" in line and i + 1 < n and re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", lines[i + 1]):
                head = _cells(line)
                i += 2
                rows = []
                while i < n and "|" in lines[i] and lines[i].strip():
                    rows.append(_cells(lines[i]))
                    i += 1
                t = "<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                for r in rows:
                    r = (r + [""] * len(head))[:len(head)]
                    t += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
                out.append(t + "</tbody></table>")
                continue
            if line.lstrip().startswith(">"):
                buf = []
                while i < n and lines[i].lstrip().startswith(">"):
                    buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                    i += 1
                out.append("<blockquote>" + md_to_html("\n".join(buf)) + "</blockquote>")
                continue
            m = is_item.match(line)
            if m:
                base = len(m.group(1))
                ordered = m.group(2)[0].isdigit()
                items = []
                while i < n:
                    mm = is_item.match(lines[i])
                    if mm and len(mm.group(1)) == base and mm.group(2)[0].isdigit() == ordered:
                        items.append([mm.group(3)])
                        i += 1
                        continue
                    if not lines[i].strip():
                        j = i + 1
                        if j < n and (len(lines[j]) - len(lines[j].lstrip()) > base) and lines[j].strip():
                            items[-1].append("")
                            i += 1
                            continue
                        mm2 = is_item.match(lines[j]) if j < n else None
                        if mm2 and len(mm2.group(1)) == base and mm2.group(2)[0].isdigit() == ordered:
                            i += 1
                            continue
                        break
                    indent = len(lines[i]) - len(lines[i].lstrip())
                    if indent > base or (not is_item.match(lines[i]) and not lines[i].lstrip().startswith(("#", ">", "|"))):
                        items[-1].append(lines[i][min(indent, base + 3):] if indent > base else lines[i].strip())
                        i += 1
                        continue
                    break
                tag = "ol" if ordered else "ul"
                parts = []
                for it in items:
                    inner = md_to_html("\n".join(it))
                    if inner.count("<p>") == 1 and inner.startswith("<p>"):
                        inner = re.sub(r"^<p>(.*?)</p>", r"\1", inner, flags=re.S)
                    parts.append(f"<li>{inner}</li>")
                out.append(f"<{tag}>" + "".join(parts) + f"</{tag}>")
                continue
            buf = []
            while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*```|\s*>|\s*([-*+]|\d+[.)])\s)", lines[i]):
                if "|" in lines[i] and i + 1 < n and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
                    break
                buf.append(lines[i])
                i += 1
            if buf:
                out.append("<p>" + _inline("\n".join(buf)) + "</p>")
            else:
                i += 1
        return "\n".join(out)

# ------------------------------------------------------------- preprocessing


def callouts_to_html(text, labels):
    """Turn > [!TYPE] blocks into <div class="callout ..."> before Markdown."""
    lines = text.split("\n")
    out, i = [], 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*(```|~~~)", line):
            in_code = not in_code
        m = None if in_code else re.match(r"^\s*>\s*\[!([^\]]+)\]\s*(.*)$", line)
        if not m:
            out.append(line)
            i += 1
            continue
        kind = m.group(1).strip().upper()
        css = CALLOUTS.get(kind, "note")
        title = labels.get(css, kind.capitalize()) if kind in CALLOUTS else kind.capitalize()
        body = [m.group(2)] if m.group(2).strip() else []
        i += 1
        while i < len(lines) and lines[i].lstrip().startswith(">"):
            body.append(re.sub(r"^\s*>\s?", "", lines[i]))
            i += 1
        inner = md_to_html(callouts_to_html("\n".join(body), labels))
        out += ["", f'<div class="callout callout-{css}" role="note"><div class="callout-title">{title}</div>'
                + inner.replace("\n\n", "\n") + "</div>", ""]
    return "\n".join(out)


def plain_text(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def postprocess(body, md_to_html_names, labels):
    seen = {}
    toc = []

    def heading(m):
        level, attrs, content = m.group(1), m.group(2) or "", m.group(3)
        base = slug(plain_text(content)) or "section"
        k = seen.get(base, 0)
        seen[base] = k + 1
        anchor = base if k == 0 else f"{base}-{k}"
        if level in ("2", "3"):
            toc.append((int(level), anchor, plain_text(content)))
        link = (f' <a class="anchor" href="#{anchor}" aria-label="{labels["anchor"]}">#</a>'
                if level != "1" else "")
        return f'<h{level} id="{anchor}"{attrs}>{content}{link}</h{level}>'

    body = re.sub(r"<h([1-6])(\s[^>]*)?>(.*?)</h\1>", heading, body, flags=re.S)

    def link(m):
        attr, target = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|tel:|#|data:)", target):
            return m.group(0)
        file_part, sep, anchor = target.partition("#")
        name = Path(file_part).name
        if file_part.endswith(".md"):
            file_part = md_to_html_names.get(name, name[:-3] + ".html")
        file_part = re.sub(r"^(\.\./)+screenshots/", "screenshots/", file_part)
        return f'{attr}="{file_part}{sep}{anchor}"'

    body = re.sub(r'(href|src)="([^"]+)"', link, body)
    # In numbered steps, the result written on the next line gets its own line
    body = re.sub(r"<ol>.*?</ol>",
                  lambda m: re.sub(r"\n[ \t]*(?=[^\s<]|<(?:strong|em|code|a)\b)", "<br>\n", m.group(0)),
                  body, flags=re.S)
    # Key/value tables with an empty header ("| | |"): drop the header row
    body = re.sub(r"<thead>\s*<tr>(?:\s*<th[^>]*>\s*</th>)+\s*</tr>\s*</thead>", "", body)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    body = body.replace("<img ", '<img loading="lazy" ')
    return body, toc


def toc_html(toc, labels):
    if not toc:
        return ""
    parts = [f'<div class="toc"><h2>{labels["on_this_page"]}</h2><ul>']
    nested = False
    for level, anchor, text in toc:
        if level == 3 and not nested:
            parts.append("<ul>")
            nested = True
        elif level == 2 and nested:
            parts.append("</ul>")
            nested = False
        parts.append(f'<li><a href="#{anchor}">{html.escape(text)}</a></li>')
    if nested:
        parts.append("</ul>")
    parts.append("</ul></div>")
    return "".join(parts)


def title_and_summary(text, default):
    no_comments = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    m = re.search(r"^#\s+(.+)$", no_comments, re.M)
    title = m.group(1).strip() if m else default
    summary = ""
    for block in re.split(r"\n\s*\n", no_comments[m.end():] if m else no_comments):
        b = block.strip()
        if b and not b.startswith(("#", "|", ">", "-", "*", "<", "1.")):
            summary = re.sub(r"[*_`]", "", b).replace("\n", " ")
            break
    return re.sub(r"[*_`]", "", title), summary[:180]


def main():  # noqa: C901
    setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", help="manual-docs folder")
    ap.add_argument("--title", help="Application name for the header")
    ap.add_argument("--out", help="Output folder (default manual-docs/html)")
    ap.add_argument("--language", help="Interface labels language: en or es (default: state.json)")
    args = ap.parse_args()

    docs = Path(args.docs).resolve()
    manuals = list_manuals(docs)
    if not manuals:
        print(f"ERROR: no .md files in {docs / 'manuals'}", file=sys.stderr)
        return 2
    out = Path(args.out).resolve() if args.out else docs / "html"
    out.mkdir(parents=True, exist_ok=True)

    state = {}
    state_path = docs / "_work" / "state.json"
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    project = state.get("project", {})
    site_title = args.title or project.get("name") or "User manual"
    lang = (args.language or project.get("language") or "en").lower()
    labels = LABELS.get(lang[:2], LABELS["en"])
    version = project.get("documented_version", "")
    meta = f"{labels['version']}: {html.escape(version)}" if version else ""

    css = (SKILL_DIR / "assets" / "html" / "manual.css").read_text(encoding="utf-8")
    page = Template((SKILL_DIR / "assets" / "html" / "page.html").read_text(encoding="utf-8"))

    has_index = any(p.name == "00-index.md" for p in manuals)
    names = {}
    docs_info = []
    for p in manuals:
        html_name = "index.html" if p.name == "00-index.md" else p.with_suffix(".html").name
        if not has_index and p.name == "index.md":
            html_name = "home.html"
        names[p.name] = html_name
        text = p.read_text(encoding="utf-8")
        t, s = title_and_summary(text, p.stem)
        docs_info.append({"md": p, "html": html_name, "title": t, "summary": s, "text": text})

    def doc_nav(current):
        items = []
        if not has_index:
            cls = ' class="current"' if current == "index.html" else ""
            items.append(f'<li><a href="index.html"{cls}>{labels["home"]}</a></li>')
        for d in docs_info:
            cls = ' class="current" aria-current="page"' if d["html"] == current else ""
            items.append(f'<li><a href="{d["html"]}"{cls}>{html.escape(d["title"])}</a></li>')
        return f'<h2>{labels["documents"]}</h2><ul>' + "".join(items) + "</ul>"

    def render(page_title, current, body, toc="", prev_next=""):
        return page.safe_substitute(
            LANG=lang, PAGE_TITLE=html.escape(page_title), SITE_TITLE=html.escape(site_title), META=meta,
            CSS=css, DOC_NAV=doc_nav(current), TOC=toc, BODY=body, PREV_NEXT=prev_next,
            DATE=dt.date.today().isoformat(), SKIP_LABEL=labels["skip"], MENU_LABEL=labels["menu"],
            NAV_LABEL=labels["nav"], GENERATED_LABEL=labels["generated"],
        )

    for k, d in enumerate(docs_info):
        body = md_to_html(callouts_to_html(d["text"], labels))
        body, toc = postprocess(body, names, labels)
        prev = docs_info[k - 1] if k > 0 else None
        nxt = docs_info[k + 1] if k + 1 < len(docs_info) else None
        nav = f'<nav class="prev-next" aria-label="{labels["prev_next"]}">'
        nav += f'<a href="{prev["html"]}">← {html.escape(prev["title"])}</a>' if prev else "<span></span>"
        nav += f'<a href="{nxt["html"]}">{html.escape(nxt["title"])} →</a>' if nxt else "<span></span>"
        nav += "</nav>"
        (out / d["html"]).write_text(
            render(f"{d['title']} · {site_title}", d["html"], body, toc_html(toc, labels), nav), encoding="utf-8")

    if not has_index:
        cards = "".join(
            f'<a class="card" href="{d["html"]}"><strong>{html.escape(d["title"])}</strong>'
            f'<span>{html.escape(d["summary"])}</span></a>' for d in docs_info)
        body = f"<h1>{html.escape(site_title)}</h1><p>{labels['cover_intro']}</p><div class=\"cards\">{cards}</div>"
        (out / "index.html").write_text(render(site_title, "index.html", body), encoding="utf-8")

    shots = docs / "screenshots"
    if shots.exists() and any(shots.iterdir()):
        shutil.copytree(shots, out / "screenshots", dirs_exist_ok=True)

    print(f"HTML built with {ENGINE}: {len(docs_info)} documents in {out}")
    print(f"Home page: {out / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
