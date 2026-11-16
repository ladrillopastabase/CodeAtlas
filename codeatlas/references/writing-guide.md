# Writing guide

Goal: manuals that are rich in content but easy to understand for people with
no technical background, so they can use the application on their own.

## 1. Principles

1. **Reader with no context.** Do not assume they know the architecture,
   technical jargon or the organization's internal processes.
2. **Literal precision.** Names of buttons, fields, menus, tabs and messages
   are written exactly as they appear in the interface: interface elements in
   **bold**, messages in quotes.
3. **One action per step.** Each numbered step holds one action followed by
   what happens.
4. **Action, result and restriction are kept apart.** Action: imperative
   ("Click **Save**"). Result: indicative ("The system shows…"). Restriction:
   callout or table.
5. **Explain the why when it helps.** One sentence of context ("This step
   prevents…") reduces mistakes.
6. **Realistic examples** with clearly generic fictional data, never real
   personal data.
7. **Consistent tone.** Address the reader the same way across all documents
   (by default, second person: "you").
8. **Manual language.** Write in the language chosen in phase 0. If it is not
   English, translate the prose only: interface labels and messages are
   always quoted literally from the code or its translation files.

## 2. Formatting conventions

| Element | Format | Example |
|---|---|---|
| Button, link, field, tab | Bold | Click **Submit request** |
| Navigation path | Bold with › | **Requests › New request** |
| System message | Quotes and italics | *"Your request was submitted."* appears |
| Value to type | Inline code | Type `2025-03-31` |
| Key | Inline code | Press `Enter` |

Callouts (rendered as boxes in the HTML):

```markdown
> [!WARNING]
> This action permanently deletes the record and cannot be undone.

> [!IMPORTANT]
> You can edit the request only while it is in the **Draft** state.

> [!NOTE]
> The list refreshes automatically every 5 minutes.

> [!TIP]
> Use the **Status** filter to see only pending requests.

> [!TO VERIFY]
> The code does not confirm whether the notification email also goes to the
> supervisor. Check with the responsible team.

> [!SCREENSHOT PENDING]
> **New request** screen with the full form; highlight the required fields
> and the **Submit request** button.
```

Use `WARNING` for every irreversible or sensitive operation, or one that
affects other people: deleting, voiding, approving payments, sending
communications, changing permissions, closing periods, bulk imports.

## 3. Structure of a procedure

Follow `assets/templates/procedure.md`. Rules:

- Title with an infinitive verb and an object: "Create a request", not
  "Requests" or "Creation".
- Short opening block: goal, roles, location, prerequisites.
- Numbered steps; after each step, the visible result.
- Field table after the steps (or inside the form step if it is short).
- Validation, message and problem sections only when they have content.

## 4. Banned vague phrases and their replacements

| Avoid | Write instead |
|---|---|
| "Fill in the relevant data" | Each field: "In **Start date**, pick a date after today" |
| "Fill in the form" | Field table with format and whether it is required |
| "Configure as appropriate" | Which option to pick in each case |
| "Take the necessary actions" | The concrete steps |
| "If necessary" | The concrete condition: "If the request exceeds 1,000,000" |
| "Etc." | The full list, or "among others" with a pointer to the table |
| "The system will do what is needed" | The concrete result |
| "Enter the requested information" | Which information, in which field and with what format |
| "Contact the administrator" (alone) | What exactly to ask for and what data to provide |

`validate_manuals.py` detects these expressions (in English and Spanish) and
similar ones.

## 5. Technical language

- Do not mention classes, functions, tables, endpoints, HTTP codes, variable
  names or file paths in the visible text.
- Translate concepts: "error 403" → "you do not have permission to do this";
  "record in the database" → "the request is saved"; "cron job" → "daily
  automatic process".
- If a technical term is unavoidable (CSV import format, QR code, two-factor
  token), explain it on first use and add it to the glossary.

## 6. Describing fields

For each field, state at least:

| Field | Required | Description | Format and rules | Example |
|---|---|---|---|---|
| **Email** | Yes | Address where you will receive notifications | name@domain format; up to 120 characters; must not be registered already | `ana.perez@example.com` |

Also state: dropdown values (literal), default value, whether it can be
changed later and dependencies ("appears only if **Company** is chosen in
**Type**").

## 7. Example of a bad and a good procedure

Bad:

```markdown
## Requests
To create a request, go to the module, fill in the data and save.
```

Good:

```markdown
### Create a request
<!-- F-001 -->

**Goal:** register a new purchase request for approval.
**Roles:** Requester, Supervisor.
**Location:** **Requests › New request**.
**Prerequisites:** a cost center assigned to your profile.

1. In the side menu, click **Requests**.
   Your list of requests opens.
2. Click **New request**.
   The empty form opens.
3. In **Description**, type the reason for the purchase (10 to 500 characters).
4. In **Estimated amount**, type the value with no separators or symbols (for example, `250000`).
5. Click **Submit request**.
   The message *"Your request was submitted."* appears and the request moves
   to the **Submitted** state, waiting for the Supervisor.

> [!IMPORTANT]
> Requests over 1,000,000 also need approval from Management.
```

## 8. Length and clarity

- Prefer complete manuals; never drop features to make them shorter.
- Keep clarity with a heading hierarchy (at most 4 levels), paragraphs of 2–4
  sentences, tables for comparable data and lists for steps.
- At the start of each long chapter, one paragraph explaining what it holds.
- Cross-references as links: "See
  [Approve a request](20-module-requests.md#approve-a-request)".
