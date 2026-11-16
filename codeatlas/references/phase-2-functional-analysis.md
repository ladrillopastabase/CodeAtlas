# Phase 2. Functional analysis

Goal: rebuild each feature as the user experiences it, with code evidence for
every statement.

## 1. Tracing a feature (the full chain)

For each action, follow and note each link with file and lines:

```
Entry point (menu, button, link, URL, notification)
  → Screen / component (what is shown, under what conditions)
    → Interaction (fields, buttons, confirmations)
      → Client-side validation
        → Call (method + URL)
          → Backend route → middleware / guard (authentication, role, ownership)
            → Controller → server-side validation
              → Service / business rules → effects (DB, email, queue, integration)
                → Response (success or error, code, message)
                  → What the user sees (message, redirect, state change, download)
```

If a link cannot be found, note the gap and mark the feature as `inferred` or
`unverified`. Never fill gaps with assumptions.

## 2. What to record per feature

Use `assets/templates/module-analysis.md` as a guide. At minimum:

- **Visible name** and goal for the user.
- **Exposure**: `ui`, `backend-only` (exists on the server but no screen
  calls it), `automatic` (scheduled job, event) or `integration` (triggered or
  received by an external system).
- **Location**: visible navigation path (Menu › Submenu › Tab) and URL.
- **Preconditions**: session, role, record state, prior data, configuration,
  subscription plan.
- **Fields**: literal label, control type, required, format, minimum and
  maximum, allowed values (list options), default value, dependency on other
  fields, whether it can be edited after creation.
- **Actions**: literal button or link, what it does, whether it asks for
  confirmation, whether it can be undone, whether it shows only in certain
  states or roles.
- **Validations**: client and server; literal message text.
- **Result**: what changes, where it redirects, who is notified.
- **Messages**: success, error, warning, information.
- **States** affected and the transition caused.
- **Exceptions** (see the list in section 4).

## 3. States and life cycles

For each entity with a state field (`status`, `state`, enums, state
machines):

1. List every state with its visible label.
2. List transitions: from state, to state, action that causes it, who can run
   it, conditions and effects (notifications, edit locks).
3. Identify final states and which actions stop being available.
4. Identify automatic transitions (expirations, scheduled jobs).

Record them in `state.json` → `states`. In the manual, show them as a table
and, when it helps, as a simple text diagram.

## 4. Scenarios and exceptions to look for

For each feature, check in the code whether it exists and how it responds:

| Scenario | What to look for in the code |
|---|---|
| Required fields | `required`, `NotNull`, `nullable: false`, schema rules |
| Badly formatted data | `pattern`, `email`, `regex`, types, date ranges |
| Lengths and ranges | `min`, `max`, `size`, `between` |
| Duplicate records | unique indexes, `unique`, `exists` checks before creating |
| Incomplete information | save as draft, wizard steps, per-step validation |
| Insufficient permissions | 401/403, guards, hidden or disabled buttons |
| State that blocks the action | `if status ==` conditions, buttons disabled by state |
| Forbidden operations | methods that raise business exceptions |
| Processing errors | `catch`, integration errors, timeouts, retries |
| State changes | transitions (section 3) |
| Cancellations | `cancel`, `void`, `revert` actions and their conditions |
| Reprocessing | `retry`, `reprocess`, resends, error queues |
| Deletions | hard vs soft delete (`deleted_at`), cascades |
| Confirmations | confirmation dialogs, double checks, codes |
| Role restrictions | differences in the permission matrix |
| Limits and quotas | file count and size limits, record limits, plans |
| Concurrency | locks, versioning, "another user changed this" |
| Session | expiry, automatic sign-out, lockout after failed attempts |
| Special business cases | explicit business conditions in services |

When the code does not show how the system responds, write
`> [!TO VERIFY]` in the manual with the specific question and record it in
`open_questions`.

## 5. Features that are not exposed

Compare the list of backend routes with the calls the interface makes. Routes
with no call from the interface are candidates for `backend-only`. Before
classifying them:

- Look for dynamic calls (URLs built from variables), generated clients
  (OpenAPI), mobile apps or other frontends.
- Check whether an integration, webhook or job uses them.

`backend-only` features are not documented as procedures for end users; they
are listed in the coverage section of the delivery summary and, if a
technical profile uses them (integrator, API client), in a specific appendix
for that profile.

## 6. Automatic processes and integrations

For each scheduled job, queue or event:

- What triggers it (schedule, event, user action).
- What changes for the user (state, notification, email, file available).
- How long it takes or when it happens, if the code says.

For each external integration (payments, e-signature, email, storage, ERP,
external sign-in): what the user sees, what data is sent or received, what
happens if it fails and how it is retried. Do not put credentials or internal
configuration details in end-user manuals; do put them in the administration
guide when the administrator manages them from the interface.

## 7. Output per module

- `_work/analysis/M-xx.md` with notes and evidence.
- Update in `state.json`: `screens`, `features`, `messages`, `states`,
  `open_questions`.
- Entry in `log.md`: module closed, number of features, open questions, next
  module.
