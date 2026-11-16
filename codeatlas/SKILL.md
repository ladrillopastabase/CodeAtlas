---
name: codeatlas
description: >-
  Analyzes an application's source code (frontend, backend, routes, roles,
  permissions, forms, validations, states, messages and integrations) and
  produces verifiable, traceable end-user manuals in Markdown and HTML:
  a general manual, per-role or per-module manuals, quick-start,
  administration and troubleshooting guides. Use when the user asks for a
  "user manual", "end-user documentation", "functional documentation",
  "user guide", "how-to guide for each role", or "manual de usuario" based on
  a repository or code folder, or wants to resume or extend a manual in
  progress (a manual-docs folder). Do NOT use for developer documentation
  (API reference, README, docstrings, architecture docs) or for writing
  manuals without access to the source code.
license: MIT
compatibility: >-
  Needs read access to the source code and Python 3.8 or later for the
  scripts (standard library only; the optional markdown package improves the
  HTML). Real screenshots need a running instance of the application and a
  browser that can be controlled.
metadata:
  author: ladrillopastabase
  version: 1.0.0
  category: documentation
  tags: [user-manual, functional-documentation, code-analysis, roles-and-permissions]
---

# CodeAtlas: user manuals from source code

This skill turns an application's code into user manuals that match how the
software really behaves, organized by user role and checkable against the
code.

## Critical rules (read before starting)

1. **Never invent.** No button, field, screen, message, role, state or rule is
   documented without evidence in the code. When something cannot be
   confirmed, write `> [!TO VERIFY]` with the specific open question.
2. **Evidence before writing.** Every feature is first recorded in the
   inventory (`_work/state.json`) with its evidence (file and lines) and its
   certainty level. Only then is it written up.
3. **Read the code, not just the names.** Follow each flow from the interface
   to the backend and to storage: what it does, when it runs, what conditions
   it requires and what result it produces.
4. **Separate what users can see from what they cannot.** Tell apart features
   exposed in the interface, backend-only features, automatic processes and
   integrations. Never present end users with something they cannot use.
5. **The manual is for users, not developers.** Technical traceability lives
   in the inventory and in hidden markers `<!-- F-012 -->`; the visible text
   does not mention classes, functions, tables or endpoints unless there is a
   concrete reason.
6. **Save progress to disk.** On medium and large projects, save the state
   after finishing each module. Conversation memory is not a safe place for
   the inventory.
7. **Use literal text.** Labels of buttons, fields, menus and messages are
   copied exactly as they appear in the code or in the translation files for
   the manual's language.

## Skill resources

| Resource | When to read it |
|---|---|
| `references/phase-1-reconnaissance.md` | When starting to analyze a project |
| `references/patterns-by-technology.md` | To know where routes, roles, validations and messages live in each framework |
| `references/phase-2-functional-analysis.md` | To rebuild features, flows, states and exceptions |
| `references/phase-3-user-roles.md` | To discover every role, including the non-obvious ones, and build the permission matrix |
| `references/state-and-traceability.md` | `state.json` schema, IDs, certainty, log and module-by-module work |
| `references/documentation-strategy.md` | To decide which manuals to produce and how to avoid duplication |
| `references/writing-guide.md` | Before writing any procedure |
| `references/phase-6-validation.md` | Quality checklist before delivery |
| `references/screenshots.md` | When there is (or is not) a running instance |
| `references/testing-the-skill.md` | For whoever maintains or improves this skill |
| `assets/templates/` | Templates for each kind of manual and for a procedure |
| `scripts/` | Deterministic automation (see below) |

Scripts (all accept `--help`). `SKILL_DIR` means the folder that holds this
`SKILL.md` (in Claude Code it is also available as `${CLAUDE_SKILL_DIR}`):

| Script | Purpose |
|---|---|
| `scripts/init_workspace.py PROJECT` | Creates `manual-docs/` with `state.json`, the log and folders |
| `scripts/scan_project.py PROJECT` | Detects technologies, modules, routes, candidate roles, messages and tests |
| `scripts/coverage_report.py manual-docs` | Writes `COVERAGE.md`: what is documented and what is missing |
| `scripts/validate_manuals.py manual-docs` | Automated quality control (traceability, vagueness, technical jargon, links, invented labels) |
| `scripts/build_html.py manual-docs` | Builds the navigable HTML site from the Markdown |

## Workflow

Work in seven phases. Do not skip phases: each one feeds the next. Keep a
visible task list with the phases and modules.

### Phase 0. Prepare the workspace

1. Confirm the project path and the manuals' language (by default, the
   language of the application's interface, or the user's language).
2. If `manual-docs/_work/state.json` already exists, **this is a resumed
   job**: read `state.json` and `log.md`, run `coverage_report.py` and resume
   at the first pending module or feature. Do not re-analyze validated work.
3. Otherwise run:
   ```bash
   python SKILL_DIR/scripts/init_workspace.py PROJECT_PATH --language en
   ```
   Expected result: `PROJECT_PATH/manual-docs/` with `_work/`, `manuals/`,
   `screenshots/` and `html/`. If the project is read-only, pass `--out` to
   create the workspace elsewhere.

### Phase 1. Project reconnaissance

1. Run the scanner and read its full report:
   ```bash
   python SKILL_DIR/scripts/scan_project.py PROJECT_PATH --out manual-docs/_work/reconnaissance
   ```
   It writes `reconnaissance.md` and `reconnaissance.json` with technologies,
   structure, candidate routes, role and permission terms, translation files,
   tests and existing documentation.
2. The scanner is heuristic: its results are **leads, not facts**. Open the
   files it points to and confirm.
3. Read existing documentation (README, docs, wikis in the repository) for
   context, but the code wins when they disagree; record the contradiction in
   the log.
4. Identify functional modules (groupings a user would recognize, not
   necessarily a folder) and record them in `state.json` with IDs `M-01`,
   `M-02`…
5. Size the project (see `references/state-and-traceability.md`) and, if it
   is medium or large, plan the analysis module by module.

Details: `references/phase-1-reconnaissance.md` and
`references/patterns-by-technology.md`.

### Phase 2. Functional analysis (per module)

For each module, in priority order:

1. List the screens or views (`P-xxx`) and how users reach them (menu, link,
   redirect, direct URL).
2. For each visible action (button, link, context menu, shortcut), follow the
   full chain: component → call → backend route → controller → service →
   validations → storage → response → what the user sees.
3. Record form fields with literal label, type, required or optional, format,
   limits, allowed values and default value, comparing client and server
   validation.
4. Record messages (`MSG-xxx`) with their literal text and when they appear.
5. Record states and transitions of each entity that has a life cycle.
6. Record automatic processes (scheduled jobs, queues, emails, webhooks) and
   external integrations, noting how users perceive them.
7. Mark capabilities with no reachable interface as `backend-only`.
8. Save the module notes to `_work/analysis/M-xx.md` and update `state.json`
   **before moving to the next module**. Add an entry to the log.

Details and the list of exceptions to look for:
`references/phase-2-functional-analysis.md`.

### Phase 3. User role analysis

1. Find explicit roles (enums, tables, constants, decorators, policies)
   **and** implicit profiles: anonymous visitor, newly registered or
   unverified user, record owner, guest, user from another organization or
   tenant, subscription plan, workflow approver, locked account, technical
   superuser, API client, and the system itself.
2. Rebuild permissions by checking **both layers**: what the interface hides
   and what the backend rejects. If they differ, document what the user
   experiences and record the difference as a finding.
3. Fill in the permission matrix in `state.json` (feature × role with access
   `full`, `own`, `read`, `conditional` or `denied`).
4. For each role, complete the role profile (purpose, modules, actions, data
   it can view, create, edit or delete, restrictions, processes, dependencies
   on other roles and differences).

Details: `references/phase-3-user-roles.md`.

### Phase 4. Documentation inventory

1. Run `coverage_report.py` to get the inventory, the matrix and current
   coverage.
2. Pick the documentation strategy for the application's complexity (see
   `references/documentation-strategy.md`): which manuals to produce, for whom
   and with what structure. Shared features are documented once and linked;
   per-role differences are explained in each role profile.
3. Assign each feature its target document (`doc_location`) and priority.
4. Give the user a short summary of the plan (roles found, modules, proposed
   manuals and open questions). Ask only when a question changes the scope
   (for example, whether one of the repository's apps should be documented);
   otherwise continue and record the decision in the log.

### Phase 5. Writing the manuals

1. Start from the templates in `assets/templates/`. Remove sections that do
   not apply; never leave empty sections.
2. Write each procedure following `assets/templates/procedure.md` and
   `references/writing-guide.md`: goal, roles, location, prerequisites,
   numbered steps with the expected result after each step, field table,
   buttons, validations, messages, states, exceptions and troubleshooting.
3. Put the marker `<!-- F-xxx -->` right below the heading of every documented
   feature.
4. Use the standard callouts: `> [!WARNING]` for irreversible or sensitive
   operations, `> [!IMPORTANT]`, `> [!NOTE]`, `> [!TIP]` and
   `> [!TO VERIFY]`.
5. Add real screenshots or `> [!SCREENSHOT PENDING]` following
   `references/screenshots.md`. Never use made-up images.
6. Set `doc_status` to `draft` on every feature written. Work module by
   module, saving to disk after each one.

### Phase 6. Validation

1. Run:
   ```bash
   python SKILL_DIR/scripts/validate_manuals.py manual-docs --check-literals
   python SKILL_DIR/scripts/coverage_report.py manual-docs
   ```
   Fix every error. Review every warning and either fix it or justify it.
2. Go through the checklist in `references/phase-6-validation.md`. In
   particular, reopen the code behind each procedure and check step by step
   that labels, order, validations and messages match.
3. Move to `validated` only what was checked against the code. Inferred
   content keeps its `TO VERIFY` callout.

### Phase 7. Delivery

1. Build the HTML:
   ```bash
   python SKILL_DIR/scripts/build_html.py manual-docs --title "Application name"
   ```
   Result: `manual-docs/html/index.html` with a document index and each manual
   with a side table of contents.
2. Deliver: Markdown sources (`manuals/`), HTML (`html/`), `COVERAGE.md` and a
   summary with roles found, manuals produced, coverage per module and per
   role, pending or backend-only features, open questions and limitations
   (for example, pending screenshots).

## Examples

### Example 1: full manual set for a web application

The user says: "Write the user manual for this app, one per role".

Actions:
1. `init_workspace.py` and `scan_project.py` on the repository.
2. Detects Laravel + Vue; confirms routes in `routes/web.php`, roles in an
   enum and policies in `app/Policies`.
3. Analyzes 6 modules, records 48 features, 5 explicit roles and 3 implicit
   profiles (visitor, request owner, unverified user).
4. Produces a general manual, 5 role manuals, a quick-start guide and a
   troubleshooting guide; validates, builds the HTML and reports coverage.

Result: Markdown and HTML manuals with 46 of 48 features validated and 2
marked backend-only.

### Example 2: resuming a long job

The user says: "Continue the manual, you stopped at the billing module".

Actions:
1. Reads `state.json` and `log.md`; runs `coverage_report.py`.
2. Resumes `M-04 Billing` at the first `pending` feature.
3. When done, validates only the new work and regenerates global coverage.

### Example 3: a single procedure

The user says: "Document how a supervisor approves a request".

Actions: an analysis limited to that flow (including states, permissions and
rejections), a procedure written from the template, and delivery of the
Markdown and its HTML. The full workspace can be skipped if the user does not
need it, but the evidence is kept in a traceability appendix.

## Troubleshooting

### The project is too large to read in full
Cause: thousands of files. Solution: work module by module as described in
`references/state-and-traceability.md`, save `state.json` after each module,
read only the files in each feature's chain and, if subagents are available,
delegate independent modules with instructions to return records in the
inventory format.

### No explicit roles are found
Cause: authorization may live in another service (identity provider), in the
database, or be based on record ownership. Solution: look for ownership
checks, token scopes, claims and seed data; document the derived profiles and
note the external source of roles under `TO VERIFY`.

### Client and server validations disagree
Solution: document what the user experiences (first the interface validation,
then the server's) and record the mismatch as a finding in the log and in the
delivery summary.

### Interface texts live in translation files
Solution: resolve each key in the file for the manual's language. If the
translation is missing, give the key under `TO VERIFY`; never translate freely.

### `validate_manuals.py` reports technical terms
Solution: replace them with the name users see. If they are needed (for
example, an import file format), keep them and explain them in the glossary.
Add `<!-- tech-ok -->` at the end of the line to accept a justified term.

### There is no running instance for screenshots
Solution: use `> [!SCREENSHOT PENDING]` with the screen and the elements to
highlight, and list them in the delivery summary.
