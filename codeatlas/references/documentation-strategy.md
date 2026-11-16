# Documentation strategy

Goal: decide which documents to produce, for whom and how to organize them
without duplicating or contradicting information.

## 1. Available document types

| Document | Template | Audience | Content |
|---|---|---|---|
| General manual | `general-manual.md` | Everyone | Full picture: access, navigation, modules, procedures, roles, messages, FAQ, glossary |
| Role manual | `role-manual.md` | One role | Only what that role can do, in the order it works |
| Module manual | `module-manual.md` | Users of one area | Every feature of the module with differences by role |
| Procedure guide | `procedure.md` | One task | A self-contained procedure |
| Administration guide | `admin-guide.md` | Administrators | Users, roles, settings, catalogs, parameters, auditing |
| Troubleshooting guide | `troubleshooting-guide.md` | Everyone / support | Symptom → cause → solution, system messages |
| Quick-start guide | `quick-start.md` | New users | First sign-in and the 3–5 most frequent tasks |
| Index | `index.md` | Everyone | Cover page of the set and document map |

## 2. Choosing the set for the complexity

| Situation | Recommended set |
|---|---|
| Small app, 1–2 roles | General manual (with a section per role) + quick start |
| 3–5 roles with very different tasks | General reference manual + role manuals + quick start + troubleshooting |
| Many modules used by different areas | Module manuals + short role profiles linking to modules + administration |
| Several apps with different audiences | One set per app + a shared document for common processes |
| One-off request | Procedure guide |

Whenever an administrator role has configuration features, produce the
administration guide. Whenever there are relevant error messages, produce the
troubleshooting guide (or chapter).

If the user asked for a specific format, follow it and suggest the others as a
next step.

## 3. Single source and links

- Each procedure is written **once** in its "owner" document (usually the
  module manual or the general manual).
- Role manuals include: the role profile, its working path and the procedures
  specific to the role. For shared procedures, they link to the owner
  document.
- If a role manual must stand alone (delivered separately), copy the full
  procedure, record both locations in `doc_location`, and phase 6 checks that
  both copies match.

## 4. Content order

- Role manual: in the order the role works (first sign-in → daily tasks →
  occasional tasks → exceptions).
- Module manual: view → create → edit → state actions → delete/void →
  export → exceptions.
- General manual: following the application's menu, so readers find in the
  document what they see on screen.

## 5. File names

In `manuals/`, use lowercase names with hyphens and a numeric prefix for
ordering:

```
00-index.md
01-quick-start.md
02-general-manual.md
10-role-supervisor.md
11-role-operator.md
20-module-requests.md
30-admin-guide.md
40-troubleshooting.md
90-glossary.md
```

`build_html.py` keeps this order and builds an HTML index with all of them.

## 6. Consistency across documents

- Use a single glossary and the same names for modules, buttons and fields in
  every document (the interface's literal texts).
- The documented version (commit or date) and the document version history
  are the same in every manual.
- Permission tables in each role manual must match the matrix in
  `state.json`.
