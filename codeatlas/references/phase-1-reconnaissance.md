# Phase 1. Project reconnaissance

Goal: get a reliable map of the project before reading code in detail, so the
analysis can be planned and nothing is left out.

## 1. Identify technologies

Check manifest files in the root and in subfolders (monorepos):

| File | Indicates |
|---|---|
| `package.json` | Node/JS/TS. Look at `dependencies`: react, next, vue, nuxt, @angular/core, svelte, express, @nestjs/core, fastify, koa |
| `requirements*.txt`, `pyproject.toml`, `Pipfile` | Python: django, flask, fastapi, celery |
| `composer.json` | PHP: laravel/framework, symfony |
| `pom.xml`, `build.gradle*` | Java/Kotlin: spring-boot, spring-security |
| `*.csproj`, `*.sln` | .NET: ASP.NET Core, Razor, Blazor |
| `Gemfile` | Ruby: rails, devise, pundit, cancancan |
| `go.mod` | Go: gin, echo, fiber |
| `pubspec.yaml` | Flutter/Dart (mobile app) |
| `android/`, `ios/`, `*.xcodeproj` | Native mobile apps |
| `docker-compose*.yml`, `k8s/`, `helm/` | Services that make up the system |
| `.env.example`, `config/` | Integrations and configurable features |

Record each **application** in the repository separately (for example,
customer portal, back office, API, mobile app). Each interface may have a
different audience and usually deserves its own manuals.

## 2. Analyze the structure

- Run `scripts/scan_project.py` and read `reconnaissance.md`.
- Review the tree of the main folders (2–3 levels).
- Find where these live: interface routes, backend routes, controllers,
  services, models, migrations, policies or guards, validations,
  translations, email templates, scheduled jobs and tests. Use
  `references/patterns-by-technology.md`.

## 3. Detect functional modules

A module is an area the user recognizes (for example, "Requests", "Billing",
"Users"). Sources for identifying modules, from most to least reliable:

1. The interface's menu or navigation bar (layout file or menu
   configuration): this is the user's view.
2. Interface route definitions and their groupings.
3. Feature folders (`features/`, `modules/`, Django `apps/`).
4. Backend controllers and route prefixes.
5. Data model entities.

Record them in `state.json` → `modules` with `id`, `name` (visible name),
`description`, `evidence` and `priority`. Also add cross-cutting modules:
**Access and account** (sign-in, password recovery, profile), **General
navigation**, **Notifications** and **Administration** when they exist.

## 4. Find existing documentation

Look for `README*`, `docs/`, `CHANGELOG`, business `*.md` files, specification
comments, user stories in tests (Gherkin `*.feature`). They are useful
context, but:

- The code wins over the documentation.
- End-to-end and acceptance tests are valuable evidence of real flows and of
  expected messages.
- Record contradictions in the log.

## 5. Size the work

| Size | Signals | Strategy |
|---|---|---|
| Small | fewer than 15 screens, 1–2 roles | Full analysis in one pass; one general manual with sections per role |
| Medium | 15–60 screens, 3–5 roles | Module-by-module analysis, saving after each module |
| Large | more than 60 screens, several apps or many roles | By module and by app, across several sessions and, where possible, parallel subagents |

Write the size, the module plan and its order in the log.

## Phase output

- `state.json` with `project` (name, technologies, applications, language)
  and `modules`.
- `_work/reconnaissance/` with the scanner report.
- An entry in `log.md` with findings and the plan.
