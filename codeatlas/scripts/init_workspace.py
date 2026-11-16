#!/usr/bin/env python3
"""Create the manual-docs/ workspace for documenting an application.

Usage:
    python init_workspace.py PROJECT_PATH [--out OUTPUT_PATH] [--language en]
                             [--name "App name"] [--templates]

Creates:
    manual-docs/_work/state.json       empty inventory (source of truth)
    manual-docs/_work/log.md           session log
    manual-docs/_work/reconnaissance/  scanner report
    manual-docs/_work/analysis/        notes per module
    manual-docs/manuals/               Markdown sources
    manual-docs/screenshots/           real screenshots
    manual-docs/html/                  HTML output

If state.json already exists it is kept (resuming a job).
With --templates the skill's templates are copied to _work/templates/.
"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import EMPTY_STATE, save_json, setup_output  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent


def git_version(project):
    try:
        r = subprocess.run(
            ["git", "-C", str(project), "describe", "--always", "--dirty", "--tags"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return ""


def main():
    setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="Root folder of the source code")
    ap.add_argument("--out", help="Output folder (default PROJECT/manual-docs)")
    ap.add_argument("--language", default="en", help="Language of the manuals (default en)")
    ap.add_argument("--name", default="", help="Visible name of the application")
    ap.add_argument("--templates", action="store_true", help="Copy templates to _work/templates")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"ERROR: project folder does not exist: {project}", file=sys.stderr)
        return 2
    out = Path(args.out).resolve() if args.out else project / "manual-docs"

    for sub in ["_work/reconnaissance", "_work/analysis", "manuals", "screenshots", "html"]:
        (out / sub).mkdir(parents=True, exist_ok=True)

    state_path = out / "_work" / "state.json"
    today = dt.date.today().isoformat()
    if state_path.exists():
        print(f"{state_path} already exists: kept (resuming a job).")
        print("Read _work/log.md and run coverage_report.py to resume.")
    else:
        state = json.loads(json.dumps(EMPTY_STATE))
        state["project"].update({
            "name": args.name or project.name,
            "path": str(project),
            "language": args.language,
            "documented_version": git_version(project) or f"code as of {today}",
        })
        save_json(state_path, state)
        print(f"Created {state_path}")

    log = out / "_work" / "log.md"
    if not log.exists():
        log.write_text(
            "# Documentation log\n\n"
            "Chronological session log. Read it first when resuming.\n\n"
            f"## {today} — Session 1\n"
            "- Phase: 0 (workspace setup)\n"
            f"- Project: {project}\n"
            "- Next step: run scan_project.py (phase 1)\n",
            encoding="utf-8",
        )
        print(f"Created {log}")

    if args.templates:
        dest = out / "_work" / "templates"
        shutil.copytree(SKILL_DIR / "assets" / "templates", dest, dirs_exist_ok=True)
        print(f"Templates copied to {dest}")

    print(f"\nWorkspace ready at: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
