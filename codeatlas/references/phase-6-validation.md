# Phase 6. Validation and quality control

Goal: make sure the manuals faithfully represent the application, are
complete and are easy to understand.

## 1. Automated validation

```bash
python SKILL_DIR/scripts/validate_manuals.py manual-docs --check-literals
python SKILL_DIR/scripts/coverage_report.py manual-docs
```

`validate_manuals.py` checks:

| Type | Check | Severity |
|---|---|---|
| Inventory | Valid JSON, unique IDs, existing references, valid enum values, evidence on features | Error |
| Traceability | `<!-- F-xxx -->` markers that do not exist in the inventory | Error |
| Traceability | `ui` features in `draft` or `validated` with no marker in any manual | Error |
| Traceability | Features with a marker in a manual but `doc_status` still `pending` | Warning |
| Consistency | `unverified` features documented as procedures | Error |
| Consistency | `inferred` features without a `TO VERIFY` callout in their section | Warning |
| Consistency | `backend-only` features documented in end-user manuals | Warning |
| Writing | Banned vague phrases | Warning |
| Writing | Visible technical terms (file paths, endpoints, code identifiers, HTTP codes) | Warning |
| Structure | Empty sections and unreplaced template placeholders (`{{…}}`) | Error |
| Structure | Headings that skip levels, more than one level-1 heading, unknown callout types | Warning |
| Links | Broken internal links (file or anchor) and missing images | Error |
| Literals (`--check-literals`) | Bold labels in numbered steps and quoted messages that do not appear verbatim in the code | Warning |
| Pending | Count of `TO VERIFY` and `SCREENSHOT PENDING` | Info |

Fix every error. Warnings are fixed or justified in the log.

## 2. Manual check against the code

For each procedure (starting with high priority ones):

- [ ] Reopen the files in its evidence.
- [ ] Navigation path: menu and names match the interface.
- [ ] Every step exists and is in the real order; no mandatory step is
      missing (confirmations, wizard steps).
- [ ] Every button and field label matches literally (translations included).
- [ ] Required status, formats, lengths and allowed values match client and
      server validation.
- [ ] The quoted messages exist literally.
- [ ] The listed roles match the permission matrix (interface and server).
- [ ] States and transitions match the logic.
- [ ] Documented exceptions have evidence; unconfirmed ones carry
      `TO VERIFY`.
- [ ] No invented buttons, screens, fields or behaviors.

When done, set `doc_status` to `validated`.

## 3. Completeness

- [ ] Every module in the inventory has status `analyzed`.
- [ ] Every `ui` feature is `validated`, or `excluded` with a reason.
- [ ] Every screen in the inventory appears in some procedure.
- [ ] Every role (including implicit ones) has a profile, or a reason why not.
- [ ] Every interface route found in reconnaissance is linked to a screen or
      discarded with a reason.
- [ ] Relevant error messages appear in the troubleshooting guide.
- [ ] Open questions are resolved or listed in the delivery.

## 4. Consistency and terminology

- [ ] The same element has the same name in every document.
- [ ] Procedures copied into several manuals are identical.
- [ ] Permission tables in the manuals match `state.json`.
- [ ] The glossary holds every business and technical term used.
- [ ] No contradictions between modules (for example, a state that allows
      editing in one module and not in another). If the code itself is
      contradictory, record a finding.

## 5. Readability (review as a new user)

Read one role manual "as if for the first time" and check:

- [ ] It makes sense without knowing the system or the organization.
- [ ] Every step says what to do and what should happen.
- [ ] Dangerous operations have a warning.
- [ ] No unexplained technical jargon.
- [ ] Examples help and use fictional data.

If subagents are available, give this reading to an agent that did not take
part in the writing, asking it to list the questions a new user would have.

## 6. Delivery summary

Include in the final answer:

- Documents produced and their audience.
- Roles found (explicit and implicit).
- Coverage per module and per role (from `COVERAGE.md`).
- Excluded features (backend-only, unreachable code) and why.
- Unconfirmed information (`TO VERIFY`) and open questions.
- Findings (interface/server mismatches, contradictions).
- Pending screenshots.
- Code version documented.
