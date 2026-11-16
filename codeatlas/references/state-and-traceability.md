# Work state, traceability and large projects

The on-disk inventory is the source of truth for the work. It lets the job
continue across sessions, split the analysis by module and check coverage
with scripts.

## Contents

1. Workspace layout
2. `state.json` schema
3. IDs and traceability markers
4. Certainty levels and documentation status
5. Log
6. Large projects and resuming
7. Several technologies or applications

## 1. Workspace layout

```
manual-docs/
├── _work/
│   ├── state.json           # Inventory and matrices (source of truth)
│   ├── log.md               # Chronological session log
│   ├── reconnaissance/      # Scanner report
│   └── analysis/            # Notes per module: M-01.md, M-02.md…
├── manuals/                 # Markdown sources of the manuals
│   └── (00-index.md, 02-general-manual.md, 10-role-*.md, 20-module-*.md…)
├── screenshots/             # Real screenshots of the application
├── html/                    # Output of build_html.py
└── COVERAGE.md              # Output of coverage_report.py
```

`_work/` is internal verification material: it is not delivered as a manual,
but it is kept for auditing and continuity.

## 2. `state.json` schema

Every list holds objects with an `id`. References between objects use those
IDs. Fields marked * are required.

```json
{
  "schema_version": 1,
  "project": {
    "name": "Visible application name",
    "path": "/path/to/project",
    "language": "en",
    "technologies": ["Laravel 10", "Vue 3"],
    "applications": [{"id": "A-01", "name": "Web portal", "audience": "Customers"}],
    "documented_version": "commit, tag or date"
  },
  "modules": [
    {"id*": "M-01", "name*": "Requests", "description": "",
     "application": "A-01", "priority": "high|medium|low",
     "analysis_status": "pending|in-progress|analyzed",
     "evidence": []}
  ],
  "screens": [
    {"id*": "P-001", "name*": "Request list", "module*": "M-01",
     "ui_route": "/requests", "access": "Menu › Requests",
     "evidence": []}
  ],
  "roles": [
    {"id*": "R-01", "name*": "Supervisor", "code_name": "SUPERVISOR",
     "type*": "explicit|implicit|external|system",
     "description": "", "how_obtained": "",
     "certainty*": "verified|inferred|unverified", "evidence": []}
  ],
  "features": [
    {"id*": "F-001", "name*": "Create request", "module*": "M-01",
     "description": "",
     "exposure*": "ui|backend-only|automatic|integration",
     "screens": ["P-001"], "roles": ["R-01"],
     "certainty*": "verified|inferred|unverified",
     "doc_status*": "pending|draft|validated|excluded",
     "exclusion_reason": "",
     "doc_location": ["manuals/20-module-requests.md"],
     "priority": "high|medium|low",
     "evidence*": [{"file": "app/Http/Controllers/RequestController.php",
                    "lines": "40-88", "kind": "controller", "note": ""}],
     "notes": ""}
  ],
  "permissions": [
    {"feature*": "F-001", "role*": "R-01",
     "access*": "full|own|read|conditional|denied",
     "condition": "", "evidence": []}
  ],
  "messages": [
    {"id*": "MSG-001", "text*": "Your request was submitted.",
     "type*": "success|error|warning|info|confirmation",
     "features": ["F-001"], "when": "", "evidence": []}
  ],
  "states": [
    {"entity*": "Request", "states*": ["Draft", "Submitted", "Approved"],
     "transitions": [{"from": "Draft", "to": "Submitted", "action": "Submit",
                      "roles": ["R-02"], "condition": "", "automatic": false}],
     "evidence": []}
  ],
  "open_questions": [
    {"id*": "Q-001", "question*": "", "context": "",
     "affects": ["F-001"], "status": "open|resolved", "answer": ""}
  ],
  "findings": [
    {"id*": "H-001", "type": "ui-server-mismatch|contradiction|dead-code|other",
     "description*": "", "evidence": []}
  ]
}
```

Suggested evidence kinds: `ui-route`, `component`, `template`, `api-route`,
`controller`, `service`, `model`, `migration`, `validation`, `permission`,
`translation`, `test`, `job`, `configuration`, `documentation`.

Edit `state.json` carefully: it is strict JSON. After every edit,
`validate_manuals.py --state-only` checks syntax and references.

## 3. IDs and traceability markers

- Prefixes: `A-` application, `M-` module, `P-` screen (page), `R-` role,
  `F-` feature, `MSG-` message, `Q-` question, `H-` finding.
- IDs are never reused or renumbered. If something is removed, mark it
  `excluded` with a reason.
- In the Markdown, every section that documents a feature carries the hidden
  marker right below its heading:

  ```markdown
  ### Create a request
  <!-- F-001 -->
  ```

  A section may carry several markers if it covers several features
  (`<!-- F-001 F-002 -->`). The marker is invisible in the HTML and lets
  `coverage_report.py` and `validate_manuals.py` cross-check manual and
  inventory.
- Optionally, role sections carry `<!-- R-01 -->`.

## 4. Certainty levels and documentation status

| Certainty | Meaning | Treatment in the manual |
|---|---|---|
| `verified` | The whole chain was read in the code | Write normally |
| `inferred` | Partial evidence (for example, route and screen but not the server validation) | Write what is verified and add `> [!TO VERIFY]` with what is inferred |
| `unverified` | Only hints (names, comments, old documentation) | Do not write as a procedure; list as pending |

| Doc status | Meaning |
|---|---|
| `pending` | In the inventory, not written yet |
| `draft` | Written, not yet checked in phase 6 |
| `validated` | Checked against the code in phase 6 |
| `excluded` | Not part of the user manual (give a reason: backend-only, dead code, developer feature) |

## 5. Log

`log.md` records, per session: date, phase, modules covered, decisions,
findings, open questions and the **exact next step**. It is the first thing
to read when resuming.

Entry format:

```markdown
## 2026-05-14 — Session 3
- Phase: 2 (functional analysis)
- Modules closed: M-03 Billing (12 features, 2 inferred)
- Findings: H-004 the "Void" button is shown to operators but the server rejects it
- Questions: Q-007 source of roles from the identity provider
- Next step: analyze M-04 Reports starting at P-031
```

## 6. Large projects and resuming

To avoid losing information during long analyses:

1. **Save per closed unit.** After each module, write `analysis/M-xx.md`,
   update `state.json` and the log. Never hold several modules in memory
   without saving.
2. **Read in a targeted way.** Use searches (by route, component name, call
   URL) to follow specific chains instead of reading whole folders.
3. **Summarize with evidence.** Module notes keep file and lines so you can go
   back to the code without searching again.
4. **Write per module.** One Markdown file per module makes it easy to
   resume, validate and regenerate without touching the rest.
5. **Resume from the state.** When resuming: read the log, run
   `coverage_report.py`, take the first pending item by priority.
6. **Parallel analysis (if subagents are available).** Assign independent
   modules to subagents with instructions to return records in `state.json`
   format (with evidence). Merge their results one by one, keep IDs from
   colliding (assign ranges, for example F-100–F-199 to module 2) and
   spot-check the evidence before accepting it.
7. **Final cross-cutting review.** After the modules, review flows that span
   modules (for example, a request that produces an invoice) and roles that
   appear in several modules.

## 7. Several technologies or applications

- Record each application in `project.applications` and link modules to them.
- Connect frontends and backends through each call's URL and HTTP method; if
  there is a generated client or an API gateway, use its definition (OpenAPI,
  GraphQL schema) as the bridge.
- Microservices: follow the chain to the service that applies the rule
  (events, queues, internal calls) and document only the visible effect.
- Applications with different audiences (customer portal and back office)
  usually deserve separate manuals that link to each other for shared
  processes.
- If part of the system is not in the repository (external service, private
  repository), state it as a limit of the analysis.
