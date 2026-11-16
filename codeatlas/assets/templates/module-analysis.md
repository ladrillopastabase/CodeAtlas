<!--
INTERNAL WORK TEMPLATE: ANALYSIS NOTES PER MODULE
Save as manual-docs/_work/analysis/M-xx.md. Not a deliverable for end users:
this is where files, lines, routes and technical names are recorded.
-->

# Analysis {{M-xx}} — {{Module name}}

- Application: {{A-xx}}
- Analysis date: {{YYYY-MM-DD}} · Code version: {{commit}}
- Status: {{in-progress | analyzed}}

## Entry points

| Screen | UI route | Reached from | Guard / condition | Evidence |
|---|---|---|---|---|
| {{P-xxx}} {{Name}} | `{{/route}}` | {{Menu…}} | {{auth, role}} | `{{file:lines}}` |

## Features

### {{F-xxx}} {{Name}}

- Exposure: {{ui | backend-only | automatic | integration}}
- Certainty: {{verified | inferred | unverified}}
- Chain:
  - UI: `{{component:lines}}` — button **{{literal text}}** (visible if {{condition}})
  - Call: `{{METHOD /api/...}}`
  - Route/guard: `{{file:lines}}` — {{middleware/role}}
  - Controller/service: `{{file:lines}}` — {{rules}}
  - Storage/effects: {{table, email, queue, integration}}
  - Visible response: {{message, redirect}}
- Fields:

  | Literal label | Technical name | Type | Req. | Client rules | Server rules | Default |
  |---|---|---|---|---|---|---|
  | {{Label}} | `{{field}}` | {{type}} | {{Yes/No}} | {{rules}} | {{rules}} | {{value}} |

- Messages: {{MSG-xxx}} *"{{text}}"* (`{{file:line}}`)
- States: {{transition}}
- Permissions: {{role → access, UI layer / server layer}}
- Verified exceptions: {{list}}
- Questions: {{Q-xxx}}

## Entity states in this module

{{Entity: states, transitions, evidence}}

## Automatic processes and integrations

{{Job / event → visible effect, evidence}}

## Backend routes not used by the interface

| Route | Evidence | Classification | Reason |
|---|---|---|---|
| `{{METHOD /route}}` | `{{file:lines}}` | {{backend-only / integration / discarded}} | {{reason}} |

## Findings

- {{H-xxx}} {{description}}
