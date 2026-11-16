<!--
PROCEDURE TEMPLATE
- Replace everything between {{ }}.
- Remove optional sections (marked "if applicable") that have no content.
- The F-xxx marker goes right below the heading and is not shown in the HTML.
- Remove this comment.
-->

### {{Infinitive verb + object, e.g. "Approve a request"}}
<!-- {{F-xxx}} -->

{{One or two paragraphs: what this feature lets the user do and why it matters in their work.}}

| | |
|---|---|
| **Goal** | {{Result the user gets}} |
| **Roles** | {{Role 1, Role 2 (with differences, see the table below)}} |
| **Location** | **{{Menu › Submenu › Tab}}** |
| **Prerequisites** | {{Data or actions that must exist first}} |
| **Permissions needed** | {{Permission or condition, in the user's language}} |
| **Required state** | {{Record state that allows the action (if applicable)}} |

#### Steps

1. {{Concrete action.}}
   {{Visible result after the action.}}
2. {{Concrete action.}}
   {{Visible result.}}
3. Click **{{Button}}**.
   {{The system shows the message *"Literal text"* and …}}

> [!SCREENSHOT PENDING]
> {{Screen and elements to highlight}}

#### Form fields (if applicable)

| Field | Required | Description | Format and rules | Example |
|---|---|---|---|---|
| **{{Literal label}}** | {{Yes/No}} | {{What goes here}} | {{Type, length, range, allowed values, depends on}} | `{{value}}` |

#### Buttons and actions (if applicable)

| Button | What it does | Available when |
|---|---|---|
| **{{Label}}** | {{Effect}} | {{State or role condition}} |

#### Validations (if applicable)

- {{Rule in the user's language}} → message *"{{literal text}}"*.

#### Expected result

{{What is saved, which state it takes, who is notified, which screen it returns to.}}

#### States (if applicable)

| State before | Action | State after | Who can |
|---|---|---|---|
| **{{State}}** | **{{Action}}** | **{{State}}** | {{Roles}} |

#### Differences by role (if applicable)

| Role | Difference |
|---|---|
| {{Role}} | {{What it sees or can do differently}} |

#### Restrictions and considerations (if applicable)

> [!WARNING]
> {{Irreversible or sensitive effect, if any}}

- {{Concrete restriction}}

#### System messages (if applicable)

| Message | Type | When it appears | What to do |
|---|---|---|---|
| *"{{Literal text}}"* | {{Success/Error/Warning}} | {{Situation}} | {{Recommended action}} |

#### Common problems (if applicable)

| Symptom | Likely cause | Solution |
|---|---|---|
| {{What the user sees}} | {{Cause}} | {{Steps to fix it}} |

> [!TO VERIFY]
> {{Only if some behavior is not confirmed in the code; describe the specific question}}
