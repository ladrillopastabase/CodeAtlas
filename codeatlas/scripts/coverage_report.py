#!/usr/bin/env python3
"""Documentation coverage report (phases 4, 6 and 7).

Usage:
    python coverage_report.py manual-docs [--sync-locations] [--json]

Cross-checks the inventory (_work/state.json) with the <!-- F-xxx --> markers
in the manuals and writes manual-docs/COVERAGE.md with:
  - summary by documentation status, certainty and exposure
  - coverage per module and per role
  - permission matrix (feature × role)
  - pending items by priority, features without markers, orphan markers
  - backend-only, automatic and integration features
  - open questions and findings

--sync-locations updates doc_location in state.json from the markers found
(it changes nothing else).
"""
import argparse
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import list_manuals, load_state, marker_ids, save_json, setup_output  # noqa: E402

SHORT = {"full": "Full", "own": "Own", "read": "View", "conditional": "Cond.", "denied": "—"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
WRITTEN = ("draft", "validated")


def pct(a, b):
    return f"{(100 * a / b):.0f} %" if b else "—"


def main():  # noqa: C901
    setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", help="manual-docs folder")
    ap.add_argument("--sync-locations", action="store_true")
    ap.add_argument("--json", action="store_true", help="Also print the summary as JSON")
    args = ap.parse_args()

    docs = Path(args.docs).resolve()
    try:
        state, state_path = load_state(docs)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    features = state.get("features", [])
    modules = {m["id"]: m for m in state.get("modules", []) if "id" in m}
    roles = {r["id"]: r for r in state.get("roles", []) if "id" in r}

    locations = defaultdict(list)
    for p in list_manuals(docs):
        rel = p.relative_to(docs).as_posix()
        for i in marker_ids(p.read_text(encoding="utf-8")):
            locations[i].append(rel)
    inventory_ids = {f.get("id") for f in features}
    orphans = sorted(i for i in locations if i.startswith("F-") and i not in inventory_ids)

    if args.sync_locations:
        changed = 0
        for f in features:
            new = sorted(set(locations.get(f.get("id"), [])))
            if new and new != sorted(f.get("doc_location", [])):
                f["doc_location"] = new
                changed += 1
        save_json(state_path, state)
        print(f"doc_location updated on {changed} features.")

    documentable = [f for f in features if f.get("exposure") == "ui" and f.get("doc_status") != "excluded"]
    by_status = Counter(f.get("doc_status", "?") for f in features)
    by_certainty = Counter(f.get("certainty", "?") for f in features)
    by_exposure = Counter(f.get("exposure", "?") for f in features)
    written = [f for f in documentable if f.get("doc_status") in WRITTEN]
    validated = [f for f in documentable if f.get("doc_status") == "validated"]
    no_marker = [f for f in written if f.get("id") not in locations]

    L = []
    w = L.append
    project = state.get("project", {})
    w(f"# Documentation coverage — {project.get('name', '')}\n")
    w(f"- Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    w(f"- Code version documented: {project.get('documented_version', '—')}")
    w(f"- Modules: {len(modules)} · Roles: {len(roles)} · Screens: {len(state.get('screens', []))} · "
      f"Features: {len(features)} · Messages: {len(state.get('messages', []))}\n")

    w("## Summary\n")
    w("| Indicator | Value |\n|---|---|")
    w(f"| Documentable interface features | {len(documentable)} |")
    w(f"| Written (draft or validated) | {len(written)} ({pct(len(written), len(documentable))}) |")
    w(f"| Validated against the code | {len(validated)} ({pct(len(validated), len(documentable))}) |")
    w(f"| Pending | {sum(1 for f in documentable if f.get('doc_status') == 'pending')} |")
    w(f"| Written without a traceability marker | {len(no_marker)} |")
    w(f"| Markers with no feature in the inventory | {len(orphans)} |")
    w(f"| Open questions | {sum(1 for q in state.get('open_questions', []) if q.get('status', 'open') == 'open')} |")
    w(f"| Findings | {len(state.get('findings', []))} |\n")
    w("By documentation status: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    w("\nBy certainty: " + ", ".join(f"{k} {v}" for k, v in sorted(by_certainty.items())))
    w("\nBy exposure: " + ", ".join(f"{k} {v}" for k, v in sorted(by_exposure.items())) + "\n")

    w("## Coverage per module\n")
    w("| Module | Analysis | Feat. | UI | Written | Validated | Pending | Excluded | Coverage |")
    w("|---|---|---|---|---|---|---|---|---|")
    per_module = defaultdict(list)
    for f in features:
        per_module[f.get("module", "?")].append(f)
    for mid in list(modules) + sorted(k for k in per_module if k not in modules):
        items = per_module.get(mid, [])
        ui = [f for f in items if f.get("exposure") == "ui" and f.get("doc_status") != "excluded"]
        wr = [f for f in ui if f.get("doc_status") in WRITTEN]
        va = [f for f in ui if f.get("doc_status") == "validated"]
        pe = [f for f in ui if f.get("doc_status") == "pending"]
        ex = [f for f in items if f.get("doc_status") == "excluded"]
        m = modules.get(mid, {})
        w(f"| {mid} {m.get('name', '(not registered)')} | {m.get('analysis_status', '—')} | {len(items)} | {len(ui)} | "
          f"{len(wr)} | {len(va)} | {len(pe)} | {len(ex)} | {pct(len(wr), len(ui))} |")
    w("")

    # Access per role: from permissions; otherwise from features.roles
    access = defaultdict(dict)
    for p in state.get("permissions", []):
        access[p.get("feature")][p.get("role")] = p.get("access", "?")
    for f in features:
        for r in f.get("roles", []):
            access[f.get("id")].setdefault(r, "full")

    w("## Coverage per role\n")
    w("| Role | Type | Certainty | Features with access | Written | Validated | Coverage |")
    w("|---|---|---|---|---|---|---|")
    fmap = {f.get("id"): f for f in features}
    for rid, r in roles.items():
        reachable = [fmap[fid] for fid, d in access.items() if fid in fmap and d.get(rid, "denied") != "denied"
                     and fmap[fid].get("exposure") == "ui" and fmap[fid].get("doc_status") != "excluded"]
        wr = [f for f in reachable if f.get("doc_status") in WRITTEN]
        va = [f for f in reachable if f.get("doc_status") == "validated"]
        w(f"| {rid} {r.get('name', '')} | {r.get('type', '—')} | {r.get('certainty', '—')} | {len(reachable)} | "
          f"{len(wr)} | {len(va)} | {pct(len(wr), len(reachable))} |")
    w("")

    if roles and features:
        w("## Permission matrix\n")
        w("Full = full access · Own = own records only · View = read only · Cond. = conditional · — = no access · (blank) = not recorded\n")
        w("| Feature | " + " | ".join(roles) + " |")
        w("|---|" + "---|" * len(roles))
        for f in sorted(features, key=lambda x: (x.get("module", ""), x.get("id", ""))):
            row = [SHORT.get(access.get(f.get("id"), {}).get(rid, ""), "") for rid in roles]
            w(f"| {f.get('id')} {f.get('name', '')} | " + " | ".join(row) + " |")
        w("\nRole legend: " + "; ".join(f"{rid} = {r.get('name', '')}" for rid, r in roles.items()) + "\n")
        conditional = [p for p in state.get("permissions", []) if p.get("access") == "conditional"]
        if conditional:
            w("Conditions:\n")
            for p in conditional:
                w(f"- {p.get('feature')} / {p.get('role')}: {p.get('condition', '(not described)')}")
            w("")

    w("## Pending documentation (by priority)\n")
    pending = sorted((f for f in documentable if f.get("doc_status") == "pending"),
                     key=lambda f: (PRIORITY_ORDER.get(f.get("priority", "medium"), 1), f.get("id", "")))
    if pending:
        w("| Feature | Module | Priority | Certainty |\n|---|---|---|---|")
        for f in pending:
            w(f"| {f.get('id')} {f.get('name', '')} | {f.get('module', '')} | {f.get('priority', '—')} | {f.get('certainty', '—')} |")
    else:
        w("None.")
    w("")

    if no_marker:
        w("## Written without a traceability marker\n")
        for f in no_marker:
            w(f"- {f.get('id')} {f.get('name', '')}")
        w("")
    if orphans:
        w("## Markers with no feature in the inventory\n")
        for h in orphans:
            w(f"- {h} in {', '.join(sorted(set(locations[h])))}")
        w("")

    others = [f for f in features if f.get("exposure") in ("backend-only", "automatic", "integration")]
    w("## Features not exposed as user procedures\n")
    if others:
        w("| Feature | Exposure | Doc status | Reason / note |\n|---|---|---|---|")
        for f in others:
            w(f"| {f.get('id')} {f.get('name', '')} | {f.get('exposure')} | {f.get('doc_status', '')} | "
              f"{f.get('exclusion_reason') or f.get('notes', '')} |")
    else:
        w("None recorded.")
    w("")

    excluded_ui = [f for f in features if f.get("doc_status") == "excluded" and f.get("exposure") == "ui"]
    if excluded_ui:
        w("## Excluded interface features\n")
        for f in excluded_ui:
            w(f"- {f.get('id')} {f.get('name', '')}: {f.get('exclusion_reason', '(no reason)')}")
        w("")

    questions = [q for q in state.get("open_questions", []) if q.get("status", "open") == "open"]
    w("## Open questions\n")
    for q in questions:
        w(f"- **{q.get('id')}** {q.get('question', '')} (affects: {', '.join(q.get('affects', [])) or '—'})")
    if not questions:
        w("None.")
    w("")
    findings = state.get("findings", [])
    w("## Findings\n")
    for h in findings:
        w(f"- **{h.get('id')}** [{h.get('type', 'other')}] {h.get('description', '')}")
    if not findings:
        w("None.")
    w("")

    (docs / "COVERAGE.md").write_text("\n".join(L), encoding="utf-8")
    summary = {
        "documentable": len(documentable), "written": len(written), "validated": len(validated),
        "pending": len(pending), "without_marker": len(no_marker), "orphan_markers": len(orphans),
        "open_questions": len(questions), "findings": len(findings),
    }
    print(f"Coverage: {summary['written']}/{summary['documentable']} written "
          f"({pct(summary['written'], summary['documentable'])}), {summary['validated']} validated, "
          f"{summary['pending']} pending.")
    print(f"Report: {docs / 'COVERAGE.md'}")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
