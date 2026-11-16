# Phase 3. User roles and permissions

Goal: identify **every** kind of user who interacts with the application,
what each one can do and how they differ. The obvious roles are often only
part of the picture.

## 1. Sources of explicit roles

- Enums or constants (`Role`, `UserType`, `ROLE_*`).
- Tables and seeds (`roles`, `permissions`, `groups`, `role_user`).
- Decorators and annotations (`@Roles`, `@PreAuthorize`, `[Authorize(Roles=`).
- Policies and abilities (`Policies/`, `ability.rb`, `Gate::define`, `casl`).
- Route configuration (`meta.roles`, `data.roles`, `middleware('role:`).
- Menus filtered by role.
- External identity provider (Keycloak, Auth0, Azure AD, Cognito): roles may
  arrive in the token (`claims`, `groups`, `scope`). If they are not in the
  repository, record the source and mark it `TO VERIFY`.

## 2. Implicit profiles (always check)

These profiles do not always appear as a "role" in the code, but they have
distinct experiences and may need their own documentation:

| Profile | How to detect it |
|---|---|
| Anonymous visitor | public routes, `permitAll`, `AllowAnonymous`, pages with no guard |
| User signing up or unverified | `email_verified`, `confirmed_at`, `is_active=False`, verification screens |
| User with an expired password or first sign-in | forced password change, terms acceptance |
| Locked or suspended account | `locked`, `suspended`, failed attempts |
| Record owner | comparisons like `record.user_id == current_user.id`, `owner`, `created_by` |
| Assignee or person responsible | `assigned_to`, `owner`, `reviewer` fields |
| Workflow approver | transitions that require a position, level or amount |
| Guest or external collaborator | invitations, shared links with a token, temporary access |
| Member of another organization (multi-tenant) | `tenant_id`, `organization_id`, `company_id`; per-organization admins |
| Plan or subscription tier | `plan`, `tier`, `subscription`, per-plan limits |
| Technical superuser | `is_superuser`, `root`, the framework's admin console |
| Impersonated or impersonating user | `impersonate`, "view as" |
| API client or integrator | API tokens, keys, user-configurable webhooks |
| System (automatic processes) | jobs that act with no user; shown as "System" in histories |
| External recipient without an account | people who receive emails with action links (approve, sign, pay) |

An implicit profile is documented when it changes what the person sees or can
do. "System" is not a reader of the manual, but its actions must be explained
to the human roles they affect.

## 3. Rebuilding permissions in two layers

For each feature and each role, check:

1. **Interface layer**: is the menu, screen or button shown? Is it disabled?
   Under what condition?
2. **Server layer**: what guard, policy or check applies? What response comes
   back when it is refused?

Possible combinations and how to document them:

| Interface | Server | User experience | Action |
|---|---|---|---|
| Visible | Allowed | Can use it | Document normally |
| Hidden | Denied | Does not see it | Mention under the role's "restrictions" only if it clarifies differences |
| Visible | Denied | Sees the option but gets an error | Document the message; record a finding |
| Hidden | Allowed | Does not see it, though the server would allow it | Do not document for that role; record a finding |
| Conditional | Conditional | Depends on state, ownership or data | Document the condition in the user's language |

Access levels for the matrix: `full`, `own` (only their own records),
`read`, `conditional` (describe the condition), `denied`.

## 4. Permission matrix

Record in `state.json` → `permissions` one entry per relevant feature–role
pair, with evidence. `coverage_report.py` builds the table. In the manuals,
show a user-facing version: modules and actions per role, in plain language
(for example, "Can edit only the requests they created").

## 5. Role profile

Complete for each role (template in `assets/templates/role-manual.md`):

1. Purpose and responsibilities (inferred from what it can do; if the business
   purpose is not in the code, describe it in terms of capabilities and mark
   the rest as `TO VERIFY`).
2. How the role is obtained (who assigns it, sign-up, invitation).
3. Modules and screens available.
4. Actions it can perform.
5. Information it can view.
6. Information it can create, edit or delete.
7. Restrictions and limitations.
8. Processes it takes part in, and at which step.
9. Dependencies on other roles (who assigns it work, to whom it hands work,
   who approves what it does).
10. Differences from similar roles.

## 6. Avoiding duplication across roles

- Shared features (sign-in, own profile, search, notifications) are documented
  once in a common chapter or in the general manual, and role manuals link to
  them.
- When a feature behaves differently by role, document the procedure once and
  add a "Differences by role" table.
- A full procedure is only repeated when a role manual must stand alone (for
  example, delivered as a PDF to an external audience); in that case there is
  still a single source and consistency is checked in phase 6.
