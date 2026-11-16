#!/usr/bin/env python3
"""Automated quality control for the manuals (phase 6).

Usage:
    python validate_manuals.py manual-docs [--state-only] [--check-literals]
                               [--strict]

Checks:
  Inventory (state.json): valid JSON, required fields, unique IDs, allowed
    values, references between objects and evidence.
  Traceability: <!-- F-xxx --> markers that do not exist; written features
    without a marker; certainty and exposure consistent with what is written.
  Structure: unreplaced {{ }} template placeholders, empty sections, skipped
    heading levels, unknown > [!TYPE] callouts.
  Writing: vague phrases and technical terms visible to the user (English and
    Spanish lists).
  Links: internal links to missing files or anchors, missing images.
  --check-literals: searches the source code (project.path) for the bold
    labels in numbered steps and the quoted messages *"..."*; reports those
    that do not appear verbatim (possible invention or free translation).

To accept a justified technical term on a line, add <!-- tech-ok --> at the
end of that line.

Output: report on the console and in manual-docs/_work/validation.md.
Exit code 1 if there are errors (or warnings with --strict).
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (CALLOUTS, ENUMS, RE_COMMENT, SCREENSHOT_MARKERS, VERIFY_MARKERS,  # noqa: E402
                     list_manuals, load_state, marker_ids, sections_by_marker, setup_output,
                     slug, strip_code_blocks)

VAGUE_PHRASES = [
    # English
    r"fill in the (?:relevant|required|necessary|corresponding) (?:data|fields|information)",
    r"(?:fill in|complete|fill out) the form",
    r"as (?:appropriate|needed|required)", r"where applicable",
    r"(?:take|perform|carry out) the (?:necessary|relevant|appropriate) (?:actions|steps|changes)",
    r"if (?:necessary|needed)", r"when necessary",
    r"enter the (?:requested|required|relevant) (?:information|data|details)",
    r"configure (?:according to your needs|as appropriate)",
    r"the system will do what is (?:needed|necessary)",
    # Spanish
    r"complete (?:los|las) (?:datos|campos|información)(?: correspondientes| necesari[oa]s| requerid[oa]s)?",
    r"llene el formulario", r"rellene el formulario", r"complete el formulario",
    r"según corresponda", r"lo que corresponda", r"cuando corresponda",
    r"(?:realice|haga|efectúe) (?:las|los) (?:acciones|pasos|cambios) (?:necesari[oa]s|pertinentes|correspondientes)",
    r"si es necesario", r"en caso de ser necesario", r"de ser necesario",
    r"ingrese (?:la|los|las) (?:información|datos) (?:solicitad[oa]s|requerid[oa]s|correspondientes)",
    r"el sistema (?:hará|realizará) lo (?:pertinente|necesario|correspondiente)",
    r"\bdatos pertinentes\b",
    # Both
    r"\betc\.?(?=\s|$)",
]
RE_VAGUE = [re.compile(p, re.I) for p in VAGUE_PHRASES]
TECHNICAL_PATTERNS = [
    (re.compile(r"/api/\S*"), "API route"),
    (re.compile(r"\b[\w./-]+\.(?:php|py|tsx?|jsx?|java|kt|cs|rb|go|vue|svelte|sql|dart)\b"), "code file"),
    (re.compile(r"\b\w+\(\)"), "function call"),
    (re.compile(r"\b[a-z]+[A-Z][a-zA-Z0-9]+\b"), "camelCase identifier"),
    (re.compile(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b"), "snake_case identifier"),
    (re.compile(r"\b(?:HTTP|error|code|status|código)\s*[45]\d\d\b", re.I), "HTTP code"),
    (re.compile(r"\b(?:endpoint|middleware|payload|controller|stack ?trace|null|undefined|backend|frontend|query)\b", re.I),
     "technical jargon"),
]
RE_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_CALLOUT = re.compile(r"^\s*>\s*\[!([^\]]+)\]")
RE_BOLD = re.compile(r"\*\*([^*]+)\*\*")
RE_MESSAGE = re.compile(r"\*[\"“]([^\"”*]{3,})[\"”]\*")
SOURCE_EXT = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html", ".py", ".php", ".java", ".kt", ".cs",
              ".cshtml", ".razor", ".rb", ".erb", ".go", ".dart", ".swift", ".json", ".yml", ".yaml", ".xml",
              ".properties", ".po", ".arb", ".resx", ".strings", ".twig", ".jinja", ".j2", ".hbs", ".ejs", ".pug"}
EXCLUDED_DIRS = {".git", "node_modules", "vendor", "dist", "build", ".next", ".nuxt", "target", "__pycache__",
                 ".venv", "venv", "coverage", "manual-docs", "bin", "obj", ".dart_tool", "Pods"}

REQUIRED = {
    "modules": ["id", "name"],
    "screens": ["id", "name", "module"],
    "roles": ["id", "name", "type", "certainty"],
    "features": ["id", "name", "module", "exposure", "certainty", "doc_status"],
    "permissions": ["feature", "role", "access"],
    "messages": ["id", "text", "type"],
    "states": ["entity", "states"],
    "open_questions": ["id", "question"],
    "findings": ["id", "description"],
}
PREFIXES = {"modules": "M-", "screens": "P-", "roles": "R-", "features": "F-",
            "messages": "MSG-", "open_questions": "Q-", "findings": "H-"}


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, where, text):
        self.items.append((level, where, text))

    def count(self, level):
        return sum(1 for i in self.items if i[0] == level)


def validate_state(state, rep):  # noqa: C901
    S = "state.json"
    if state.get("schema_version") is None:
        rep.add("ERROR", S, "Missing schema_version")
    ids = defaultdict(set)
    for name, fields in REQUIRED.items():
        items = state.get(name)
        if items is None:
            rep.add("ERROR", S, f"Missing list '{name}'")
            continue
        if not isinstance(items, list):
            rep.add("ERROR", S, f"'{name}' must be a list")
            continue
        for k, e in enumerate(items):
            if not isinstance(e, dict):
                rep.add("ERROR", S, f"{name}[{k}] is not an object")
                continue
            for c in fields:
                if e.get(c) in (None, "", []):
                    rep.add("ERROR", S, f"{name}[{k}] ({e.get('id', '?')}): missing '{c}'")
            if "id" in e:
                i = e["id"]
                if i in ids[name]:
                    rep.add("ERROR", S, f"Duplicate ID in {name}: {i}")
                ids[name].add(i)
                prefix = PREFIXES.get(name)
                if prefix and not str(i).startswith(prefix):
                    rep.add("WARNING", S, f"{i} in {name} does not use the prefix {prefix}")

    def enum(value, key, where):
        if value not in (None, "") and value not in ENUMS[key]:
            rep.add("ERROR", S, f"{where}: invalid value '{value}' (allowed: {', '.join(sorted(ENUMS[key]))})")

    for m in state.get("modules", []):
        enum(m.get("priority"), "priority", m.get("id"))
        enum(m.get("analysis_status"), "analysis_status", m.get("id"))
    for p in state.get("screens", []):
        if p.get("module") and p["module"] not in ids["modules"]:
            rep.add("ERROR", S, f"{p.get('id')}: unknown module {p['module']}")
    for r in state.get("roles", []):
        enum(r.get("type"), "role_type", r.get("id"))
        enum(r.get("certainty"), "certainty", r.get("id"))
        if not r.get("evidence") and r.get("type") != "system":
            rep.add("WARNING", S, f"{r.get('id')} {r.get('name')}: role without evidence")
    for f in state.get("features", []):
        fid = f.get("id")
        enum(f.get("exposure"), "exposure", fid)
        enum(f.get("certainty"), "certainty", fid)
        enum(f.get("doc_status"), "doc_status", fid)
        enum(f.get("priority"), "priority", fid)
        if f.get("module") and f["module"] not in ids["modules"]:
            rep.add("ERROR", S, f"{fid}: unknown module {f['module']}")
        for p in f.get("screens", []):
            if p not in ids["screens"]:
                rep.add("ERROR", S, f"{fid}: unknown screen {p}")
        for r in f.get("roles", []):
            if r not in ids["roles"]:
                rep.add("ERROR", S, f"{fid}: unknown role {r}")
        if not f.get("evidence"):
            level = "WARNING" if f.get("certainty") == "unverified" else "ERROR"
            rep.add(level, S, f"{fid} {f.get('name')}: no evidence in the code")
        else:
            for ev in f["evidence"]:
                if not isinstance(ev, dict) or not ev.get("file"):
                    rep.add("ERROR", S, f"{fid}: evidence without 'file'")
        if f.get("doc_status") == "excluded" and not f.get("exclusion_reason"):
            rep.add("WARNING", S, f"{fid}: excluded without exclusion_reason")
        if f.get("doc_status") == "validated" and f.get("certainty") == "unverified":
            rep.add("ERROR", S, f"{fid}: marked 'validated' but certainty is 'unverified'")
    for p in state.get("permissions", []):
        enum(p.get("access"), "access", f"permission {p.get('feature')}/{p.get('role')}")
        if p.get("feature") not in ids["features"]:
            rep.add("ERROR", S, f"Permission with unknown feature {p.get('feature')}")
        if p.get("role") not in ids["roles"]:
            rep.add("ERROR", S, f"Permission with unknown role {p.get('role')}")
        if p.get("access") == "conditional" and not p.get("condition"):
            rep.add("WARNING", S, f"Conditional permission without a condition: {p.get('feature')}/{p.get('role')}")
    for m in state.get("messages", []):
        enum(m.get("type"), "message_type", m.get("id"))
        for fid in m.get("features", []):
            if fid not in ids["features"]:
                rep.add("ERROR", S, f"{m.get('id')}: unknown feature {fid}")
    for q in state.get("open_questions", []):
        for ref in q.get("affects", []):
            if ref not in ids["features"] | ids["roles"] | ids["modules"]:
                rep.add("WARNING", S, f"{q.get('id')}: unknown reference {ref}")
    return ids


def anchors_of(text):
    seen, anchors = defaultdict(int), set()
    for line in strip_code_blocks(text).split("\n"):
        m = RE_HEADING.match(line)
        if m:
            base = slug(m.group(2))
            n = seen[base]
            anchors.add(base if n == 0 else f"{base}-{n}")
            seen[base] += 1
    for m in re.finditer(r"<a\s+(?:name|id)=['\"]([^'\"]+)", text):
        anchors.add(m.group(1))
    return anchors


def validate_manual(path, docs, rep, anchor_cache):  # noqa: C901
    rel = path.relative_to(docs).as_posix()
    raw = path.read_text(encoding="utf-8")
    no_code = strip_code_blocks(raw)
    visible = RE_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), no_code)
    raw_lines = raw.split("\n")
    lines = visible.split("\n")

    headings = []
    h1 = 0
    previous = 0
    for i, line in enumerate(lines):
        m = RE_HEADING.match(line)
        if m:
            level = len(m.group(1))
            headings.append((i, level, m.group(2)))
            if level == 1:
                h1 += 1
            if previous and level > previous + 1:
                rep.add("WARNING", f"{rel}:{i + 1}", f"Heading level skipped (h{previous} → h{level}): '{m.group(2)}'")
            previous = level
    if h1 > 1:
        rep.add("WARNING", rel, f"There are {h1} level-1 headings; use one per document")
    for k, (i, level, text) in enumerate(headings):
        end = headings[k + 1][0] if k + 1 < len(headings) else len(lines)
        next_level = headings[k + 1][1] if k + 1 < len(headings) else 0
        body = "\n".join(lines[i + 1:end]).strip()
        if not body and (next_level == 0 or next_level <= level):
            rep.add("ERROR", f"{rel}:{i + 1}", f"Empty section: '{text}'")

    for i, line in enumerate(lines):
        n = i + 1
        if "{{" in line and "}}" in line:
            rep.add("ERROR", f"{rel}:{n}", "Unreplaced template placeholder: " + line.strip()[:100])
        m = RE_CALLOUT.match(line)
        if m and m.group(1).strip().upper() not in CALLOUTS:
            rep.add("WARNING", f"{rel}:{n}", f"Unknown callout type: [!{m.group(1)}]")
        for rx in RE_VAGUE:
            mm = rx.search(line)
            if mm:
                rep.add("WARNING", f"{rel}:{n}", f"Vague phrase: '{mm.group(0)}'")
        if i < len(raw_lines) and "tech-ok" in raw_lines[i]:
            continue
        plain = RE_LINK.sub(lambda x: x.group(2), line)
        plain = re.sub(r"<[^>]+>", "", plain)
        plain = re.sub(r"https?://\S+|\S+@\S+\.\w+", "", plain)
        for rx, kind in TECHNICAL_PATTERNS:
            mm = rx.search(plain)
            if mm:
                rep.add("WARNING", f"{rel}:{n}", f"Visible technical term ({kind}): '{mm.group(0)}'")
                break
        for mm in RE_LINK.finditer(line):
            is_img, target = mm.group(1), mm.group(3)
            if re.match(r"^(https?:|mailto:|tel:|data:)", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = path if not file_part else (path.parent / file_part).resolve()
            if file_part and not dest.exists():
                rep.add("ERROR", f"{rel}:{n}", f"{'Image' if is_img else 'Link'} to a missing file: {target}")
                continue
            if anchor and dest.suffix == ".md":
                if dest not in anchor_cache:
                    anchor_cache[dest] = anchors_of(dest.read_text(encoding="utf-8"))
                if anchor not in anchor_cache[dest]:
                    rep.add("ERROR", f"{rel}:{n}", f"Missing anchor: #{anchor} in {file_part or rel}")
    return raw


def load_source(root):
    chunks = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for f in filenames:
            p = Path(dirpath) / f
            if p.suffix.lower() in SOURCE_EXT:
                try:
                    if p.stat().st_size < 2_000_000:
                        chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
    return "\n".join(chunks)


def check_literals(manual_texts, root, rep):
    if not root or not Path(root).is_dir():
        rep.add("WARNING", "literals", f"Cannot check: project.path does not exist ({root})")
        return
    source = load_source(root)
    for rel, text in manual_texts:
        visible = RE_COMMENT.sub("", strip_code_blocks(text))
        for n, line in enumerate(visible.split("\n"), 1):
            candidates = []
            if re.match(r"^\s*\d+\.\s", line):
                for m in RE_BOLD.finditer(line):
                    candidates += [("label", t.strip()) for t in m.group(1).split("›") if t.strip()]
            candidates += [("message", m.group(1).strip()) for m in RE_MESSAGE.finditer(line)]
            for kind, t in candidates:
                if len(t) < 2:
                    continue
                pattern = r"(?<![\w])" + re.escape(t) + r"(?![\w])"
                if re.search(pattern, source):
                    continue
                if re.search(pattern, source, re.I):
                    rep.add("INFO", f"{rel}:{n}", f"{kind.capitalize()} found only with different letter case: '{t}'")
                else:
                    rep.add("WARNING", f"{rel}:{n}", f"{kind.capitalize()} not found verbatim in the code: '{t}'")


def main():  # noqa: C901
    setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", help="manual-docs folder")
    ap.add_argument("--state-only", action="store_true", help="Validate only state.json")
    ap.add_argument("--check-literals", action="store_true", help="Search the code for the quoted labels and messages")
    ap.add_argument("--strict", action="store_true", help="Warnings also make the run fail")
    args = ap.parse_args()

    docs = Path(args.docs).resolve()
    rep = Report()
    try:
        state, _ = load_state(docs)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: state.json is not valid JSON: {e}", file=sys.stderr)
        return 1

    ids = validate_state(state, rep)

    texts = []
    if not args.state_only:
        cache = {}
        manuals = list_manuals(docs)
        if not manuals:
            rep.add("INFO", "manuals/", "No manuals yet")
        marked = defaultdict(list)
        sections = defaultdict(list)
        to_verify = screenshots = 0
        for p in manuals:
            text = validate_manual(p, docs, rep, cache)
            rel = p.relative_to(docs).as_posix()
            texts.append((rel, text))
            for i in marker_ids(text):
                marked[i].append(rel)
            for fid, secs in sections_by_marker(text).items():
                sections[fid] += secs
            to_verify += sum(text.count(m) for m in VERIFY_MARKERS)
            screenshots += sum(text.count(m) for m in SCREENSHOT_MARKERS)

        known = ids["features"] | ids["roles"] | ids["modules"] | ids["screens"]
        for i, files in sorted(marked.items()):
            if i not in known:
                rep.add("ERROR", ", ".join(sorted(set(files))), f"Marker {i} does not exist in the inventory")
        for f in state.get("features", []):
            fid, status, cert, expo = f.get("id"), f.get("doc_status"), f.get("certainty"), f.get("exposure")
            in_manual = fid in marked
            if expo == "ui" and status in ("draft", "validated") and not in_manual:
                rep.add("ERROR", fid, f"'{f.get('name')}' is '{status}' but has no marker in any manual")
            if in_manual and status == "pending":
                rep.add("WARNING", fid, "Has a marker in a manual but doc_status is 'pending' (update state.json)")
            if in_manual and status == "excluded":
                rep.add("WARNING", fid, "Is excluded but appears in a manual")
            if in_manual and cert == "unverified":
                rep.add("ERROR", fid, "'unverified' feature documented as a procedure")
            if in_manual and expo == "backend-only":
                rep.add("WARNING", fid, "Backend-only feature documented in a user manual")
            if cert == "inferred" and fid in sections and not any(
                    any(m in s for m in VERIFY_MARKERS) for s in sections[fid]):
                rep.add("WARNING", fid, "Certainty 'inferred' without a [!TO VERIFY] callout in its section")
        rep.add("INFO", "pending", f"TO VERIFY callouts: {to_verify} · SCREENSHOT PENDING: {screenshots}")

        if args.check_literals:
            check_literals(texts, state.get("project", {}).get("path"), rep)

    order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    items = sorted(rep.items, key=lambda x: (order[x[0]], x[1]))
    L = ["# Validation report\n",
         f"- Errors: {rep.count('ERROR')}", f"- Warnings: {rep.count('WARNING')}", f"- Info: {rep.count('INFO')}\n",
         "| Level | Location | Detail |", "|---|---|---|"]
    for level, where, text in items:
        detail = text.replace("|", "\\|")
        L.append(f"| {level} | `{where}` | {detail} |")
    (docs / "_work").mkdir(exist_ok=True)
    (docs / "_work" / "validation.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    for level, where, text in items:
        print(f"[{level}] {where}: {text}")
    print(f"\nResult: {rep.count('ERROR')} errors, {rep.count('WARNING')} warnings. "
          f"Report: {docs / '_work' / 'validation.md'}")
    if rep.count("ERROR") or (args.strict and rep.count("WARNING")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
