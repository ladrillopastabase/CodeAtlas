# Testing the skill (for maintainers)

Following the recommended skill testing approach: triggering, functional
tests and performance comparison.

## 1. Triggering tests

Should trigger the skill:

- "Write the user manual for this application from the code"
- "I need a manual for each role in this system"
- "Create end-user documentation for this repository"
- "Write a how-to guide for the billing module of this project"
- "Can you document how a supervisor approves requests in this app?"
- "Genera el manual de usuario de esta aplicación a partir del código"
- "Continue the manual we were working on in manual-docs"
- "I want a quick-start guide for the platform's customers, the code is in this folder"

Should NOT trigger it:

- "Write the repository README"
- "Generate the API documentation with OpenAPI"
- "Explain how this backend's architecture works"
- "Add docstrings to these functions"
- "Write a code of conduct for the school"
- "Proofread this Word manual" (no source code)

Procedure: run each query 2–3 times in a new conversation with the skill
enabled and record whether it loaded. Target: 90 % triggering on positives
and 0 % on negatives. If it fails, adjust the frontmatter description
(keywords or negative triggers).

## 2. Functional tests

Case A — small application (for example, a CRUD with two roles):

- Given: a repository with 2 explicit roles and public routes.
- Then: both roles + anonymous visitor are identified; every interface route
  is in the inventory; `validate_manuals.py` finishes with no errors; the HTML
  is built; no documented button is missing from the code.

Case B — two-layer permissions:

- Given: a button visible to a role whose server rejects the action.
- Then: a `ui-server-mismatch` finding is recorded and the manual describes
  the real error message.

Case C — resuming:

- Given: `state.json` with two `analyzed` modules and one `pending`.
- Then: the skill resumes the pending module without re-analyzing the others.

Case D — information that cannot be verified:

- Given: an email whose recipient depends on external configuration.
- Then: `TO VERIFY` and an open question appear; the recipient is not
  invented.

No-invention check (all cases): run `validate_manuals.py --check-literals`
and, in addition, pick 10 button labels and 5 quoted messages from the manual
and search for them verbatim in the code. All must appear.

## 3. Performance comparison

Compare the same request with and without the skill: number of features
documented versus the real inventory, roles detected, number of corrections
the user needs and presence of invented elements.

## 4. Signals for iterating

- Does not trigger when it should → add keywords to the description.
- Triggers on developer documentation requests → strengthen negative
  triggers.
- Misses implicit profiles → check how section 2 of `phase-3-user-roles.md`
  is applied.
- Invents elements → strengthen phase 6 and critical rule 1.
