"""Helpers shared by the skill's scripts (standard library only)."""
import json
import re
import sys
import unicodedata
from pathlib import Path

SCHEMA_VERSION = 1

ENUMS = {
    "exposure": {"ui", "backend-only", "automatic", "integration"},
    "certainty": {"verified", "inferred", "unverified"},
    "doc_status": {"pending", "draft", "validated", "excluded"},
    "access": {"full", "own", "read", "conditional", "denied"},
    "role_type": {"explicit", "implicit", "external", "system"},
    "message_type": {"success", "error", "warning", "info", "confirmation"},
    "priority": {"high", "medium", "low"},
    "analysis_status": {"pending", "in-progress", "analyzed"},
}

EMPTY_STATE = {
    "schema_version": SCHEMA_VERSION,
    "project": {
        "name": "",
        "path": "",
        "language": "en",
        "technologies": [],
        "applications": [],
        "documented_version": "",
    },
    "modules": [],
    "screens": [],
    "roles": [],
    "features": [],
    "permissions": [],
    "messages": [],
    "states": [],
    "open_questions": [],
    "findings": [],
}

# Callout types: canonical key -> CSS class. Spanish aliases are accepted so
# manuals written in Spanish can use their own words.
CALLOUTS = {
    "NOTE": "note", "NOTA": "note",
    "TIP": "tip", "CONSEJO": "tip",
    "IMPORTANT": "important", "IMPORTANTE": "important",
    "WARNING": "warning", "CAUTION": "warning", "ADVERTENCIA": "warning",
    "TO VERIFY": "verify", "POR VERIFICAR": "verify",
    "SCREENSHOT PENDING": "screenshot", "CAPTURA PENDIENTE": "screenshot",
}
VERIFY_MARKERS = ("[!TO VERIFY]", "[!POR VERIFICAR]")
SCREENSHOT_MARKERS = ("[!SCREENSHOT PENDING]", "[!CAPTURA PENDIENTE]")

# Traceability marker: <!-- F-001 F-002 R-01 -->
RE_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
RE_ID = re.compile(r"\b(F|R|M|P)-\d{1,4}\b")
RE_FEATURE_ID = re.compile(r"\bF-\d{1,4}\b")


def setup_output():
    """Avoid encoding errors when printing accented text on limited consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def load_state(docs_dir):
    path = Path(docs_dir) / "_work" / "state.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist. Run init_workspace.py on the project first.")
    with path.open(encoding="utf-8") as f:
        return json.load(f), path


def save_json(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def slug(text):
    """GitHub-style anchor: lowercase, keeps accented letters, drops
    punctuation, turns spaces into hyphens."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_`~\[\]]", "", text)
    text = unicodedata.normalize("NFC", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def list_manuals(docs_dir):
    folder = Path(docs_dir) / "manuals"
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*.md") if p.is_file())


def strip_code_blocks(text):
    """Blank out fenced code blocks (keeps line count for line numbers)."""
    out, in_block = [], False
    for line in text.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            in_block = not in_block
            out.append("")
            continue
        out.append("" if in_block else line)
    return "\n".join(out)


def marker_ids(text):
    """Set of F-/R-/M-/P- IDs found in HTML comments (traceability markers)."""
    ids = set()
    for m in RE_COMMENT.finditer(strip_code_blocks(text)):
        body = m.group(1)
        if "{{" in body:
            continue
        ids.update(x.group(0) for x in RE_ID.finditer(body))
    return ids


def sections_by_marker(text):
    """Map each F-xxx to the text of its section (from its heading to the next
    heading of the same or higher level)."""
    lines = strip_code_blocks(text).split("\n")
    headings = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            headings.append((i, len(m.group(1))))
    result = {}
    for idx, (start, level) in enumerate(headings):
        end = len(lines)
        for j, n in headings[idx + 1:]:
            if n <= level:
                end = j
                break
        head = "\n".join(lines[start:start + 3])
        ids = set()
        for m in RE_COMMENT.finditer(head):
            ids.update(x.group(0) for x in RE_FEATURE_ID.finditer(m.group(1)))
        for fid in ids:
            result.setdefault(fid, []).append("\n".join(lines[start:end]))
    return result
