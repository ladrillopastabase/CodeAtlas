#!/usr/bin/env python3
"""Heuristic project reconnaissance (phase 1).

Usage:
    python scan_project.py PROJECT_PATH [--out FOLDER] [--max-items 300]

Writes reconnaissance.md (readable) and reconnaissance.json (structured) with:
  - technologies detected from manifest files
  - folder structure and file counts by type
  - candidate interface and backend routes (file:line)
  - HTTP calls from the frontend and backend routes with no apparent caller
  - role and permission terms, and authorization files
  - validation, translation, email, scheduled job, test and existing
    documentation files
  - environment variables that hint at integrations

IMPORTANT: the results are LEADS to direct the reading of the code. They are
not verified facts: confirm each one by opening the file.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import setup_output  # noqa: E402

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", ".next",
    ".nuxt", ".svelte-kit", "target", "bin", "obj", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "coverage", ".idea", ".vscode", "bower_components",
    ".gradle", "Pods", "DerivedData", ".dart_tool", "manual-docs", "storage", "public/build",
    ".angular", ".cache", "tmp", "logs",
}
TEXT_EXT = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".html", ".htm",
    ".py", ".php", ".java", ".kt", ".kts", ".cs", ".cshtml", ".razor", ".rb", ".erb", ".go",
    ".dart", ".swift", ".json", ".yml", ".yaml", ".xml", ".properties", ".po", ".arb",
    ".resx", ".strings", ".md", ".rst", ".txt", ".feature", ".twig", ".jinja", ".j2",
    ".hbs", ".ejs", ".pug", ".sql", ".graphql", ".gql", ".env", ".example",
    ".toml", ".cfg", ".ini", ".gradle",
}
MAX_SIZE = 1_000_000

MANIFESTS = {
    "package.json": "Node.js / JavaScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "composer.json": "PHP",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle)",
    "Gemfile": "Ruby",
    "go.mod": "Go",
    "pubspec.yaml": "Flutter / Dart",
    "Cargo.toml": "Rust",
    "docker-compose.yml": "Docker Compose (several services)",
    "docker-compose.yaml": "Docker Compose (several services)",
    "angular.json": "Angular",
    "AndroidManifest.xml": "Android",
}
FRAMEWORKS = [
    ("react", "React"), ("next", "Next.js"), ("vue", "Vue"), ("nuxt", "Nuxt"),
    ("@angular/core", "Angular"), ("svelte", "Svelte"), ("express", "Express"),
    ("@nestjs/core", "NestJS"), ("fastify", "Fastify"), ("koa", "Koa"),
    ("react-native", "React Native"), ("electron", "Electron"),
    ("django", "Django"), ("djangorestframework", "Django REST Framework"),
    ("flask", "Flask"), ("fastapi", "FastAPI"), ("celery", "Celery"),
    ("laravel/framework", "Laravel"), ("symfony/", "Symfony"),
    ("spatie/laravel-permission", "spatie/laravel-permission"),
    ("spring-boot", "Spring Boot"), ("spring-security", "Spring Security"),
    ("rails", "Ruby on Rails"), ("devise", "Devise"), ("pundit", "Pundit"),
    ("cancancan", "CanCanCan"), ("gin-gonic", "Gin"), ("labstack/echo", "Echo"),
    ("gofiber", "Fiber"), ("keycloak", "Keycloak"), ("auth0", "Auth0"),
    ("next-auth", "NextAuth"), ("passport", "Passport"), ("casl", "CASL"),
    ("react-router", "React Router"), ("react-router-dom", "React Router"), ("vue-router", "Vue Router"),
    ("i18next", "i18next"), ("vue-i18n", "vue-i18n"), ("yup", "Yup"), ("zod", "Zod"),
    ("react-hook-form", "React Hook Form"), ("formik", "Formik"),
    ("class-validator", "class-validator"), ("pydantic", "Pydantic"),
]

# (label, layer, regex) — group "path" captures the route, "method" is optional.
ROUTE_PATTERNS = [
    ("Express/Koa/Fastify", "backend",
     re.compile(r"\b(?:app|router|server|api|fastify|r)\.(?P<method>get|post|put|patch|delete|all)\(\s*['\"`](?P<path>/[^'\"`]*)")),
    ("NestJS", "backend",
     re.compile(r"@(?P<method>Get|Post|Put|Patch|Delete)\(\s*['\"]?(?P<path>[^'\")]*)")),
    ("NestJS controller", "backend", re.compile(r"@Controller\(\s*['\"](?P<path>[^'\"]*)")),
    ("Flask/FastAPI", "backend",
     re.compile(r"@\w+\.(?P<method>route|get|post|put|patch|delete|api_route)\(\s*['\"](?P<path>[^'\"]*)")),
    ("Django", "backend", re.compile(r"\b(?:re_)?path\(\s*r?['\"](?P<path>[^'\"]*)['\"]\s*,")),
    ("DRF router", "backend", re.compile(r"router\.register\(\s*r?['\"](?P<path>[^'\"]*)")),
    ("Laravel", "backend",
     re.compile(r"Route::(?P<method>get|post|put|patch|delete|resource|apiResource|any|match|view)\(\s*['\"](?P<path>[^'\"]*)")),
    ("Spring", "backend",
     re.compile(r"@(?P<method>Get|Post|Put|Patch|Delete|Request)Mapping\(\s*(?:value\s*=\s*|path\s*=\s*)?\{?\s*['\"](?P<path>[^'\"]*)")),
    ("ASP.NET", "backend", re.compile(r"\[(?P<method>Http(?:Get|Post|Put|Patch|Delete)|Route)\(\s*\"(?P<path>[^\"]*)")),
    ("ASP.NET minimal", "backend", re.compile(r"\.Map(?P<method>Get|Post|Put|Patch|Delete)\(\s*\"(?P<path>[^\"]*)")),
    ("Rails", "backend",
     re.compile(r"^\s*(?P<method>get|post|put|patch|delete|resources|resource|namespace)\s+[:'\"](?P<path>[\w/:\-]+)")),
    ("Go", "backend",
     re.compile(r"\.(?P<method>GET|POST|PUT|PATCH|DELETE|HandleFunc|Handle)\(\s*\"(?P<path>/[^\"]*)")),
    ("React Router (JSX)", "interface", re.compile(r"<Route\b[^>]*\bpath=['\"{`]+(?P<path>[^'\"}`]*)")),
    ("Router (path: object)", "interface", re.compile(r"\bpath\s*:\s*['\"`](?P<path>[^'\"`]*)['\"`]")),
    ("React Navigation", "interface", re.compile(r"<\w*\.?Screen\b[^>]*\bname=['\"](?P<path>[^'\"]+)")),
    ("Flutter", "interface", re.compile(r"['\"](?P<path>/[\w\-/:]*)['\"]\s*:\s*\(\s*context\s*\)")),
    ("GoRouter", "interface", re.compile(r"GoRoute\(\s*path\s*:\s*['\"](?P<path>[^'\"]*)")),
]
RE_HTTP_CALL = re.compile(
    r"(?:fetch|axios(?:\.(?P<method>get|post|put|patch|delete))?|http\.(?P<m2>get|post|put|patch|delete)|"
    r"api\.(?P<m3>get|post|put|patch|delete)|\$http\.(?P<m4>get|post|put|patch|delete)|useFetch|\$fetch)"
    r"\s*\(\s*['\"`](?P<path>[^'\"`]*)"
)
AUTH_PATTERNS = re.compile(
    r"(hasRole|hasAnyRole|hasAuthority|PreAuthorize|@Secured|@Roles|RolesGuard|AuthGuard|canActivate|"
    r"permission_required|login_required|permission_classes|has_perm|is_staff|is_superuser|"
    r"\bauthorize\b|Gate::|->can\(|@can|@role|middleware\(\s*['\"](?:auth|role|permission|can)|"
    r"\[Authorize|IsInRole|before_action\s*:authenticate|Pundit|CanCan|ability|"
    r"\bcan\(|usePermission|RequireAuth|PrivateRoute|ProtectedRoute|requiresAuth|meta\s*:\s*\{[^}]*roles|"
    r"checkRole|isAdmin|requireRole|roles_required|Depends\(\s*get_current)",
    re.I,
)
RE_ROLE_LITERALS = [
    re.compile(r"\bROLE_[A-Z][A-Z0-9_]+\b"),
    re.compile(r"(?:hasRole|hasAnyRole|hasAuthority|hasAnyAuthority|IsInRole|checkRole|requireRole|requireRoles|authorizeRoles|roles_required|Roles)\(([^)]*)\)"),
    re.compile(r"Roles\s*=\s*\"([^\"]+)\""),
    re.compile(r"\broles?\s*[:=]\s*\[?\s*['\"]([\w\- ]+)['\"]", re.I),
    re.compile(r"(?:role|rol|perfil|profile|user_type|usertype)\s*(?:===?|==)\s*['\"]([\w\- ]+)['\"]", re.I),
    re.compile(r"middleware\(\s*['\"]role:([\w|,\-]+)"),
    re.compile(r"\bRole\.([A-Z][A-Za-z0-9_]+)\b"),
]
RE_ROLE_ENUM = re.compile(
    r"(?:enum|class|const|let|var|type|interface)\s+(\w*(?:Role|Rol|Perfil|UserType|Profile)\w*)\b\s*(?:[=:({]|extends|\(|$)",
    re.I)

FILE_CATEGORIES = [
    ("validation", re.compile(r"(valid|request\.php$|forms?\.py$|serializers?\.py$|schema|dto)", re.I)),
    ("translation", re.compile(r"(/i18n/|/locales?/|/lang/|/l10n/|\.po$|\.arb$|\.resx$|messages[\w_]*\.properties$|Localizable\.strings$|/strings\.xml$)", re.I)),
    ("email_notification", re.compile(r"(mail|email|notification|notificacion|correo)", re.I)),
    ("automatic_jobs", re.compile(r"(cron|schedule|job|task|worker|queue|celery|listener|consumer|command)", re.I)),
    ("tests", re.compile(r"(^|/)(tests?|spec|specs|__tests__|e2e|cypress|playwright)(/|$)|\.(test|spec)\.\w+$|_test\.\w+$|\.feature$", re.I)),
    ("models", re.compile(r"(/models?/|/entities/|/entity/|models\.py$|\.entity\.ts$|/domain/)", re.I)),
    ("migrations", re.compile(r"(migration|migrations|/db/migrate/|schema\.prisma$|\.sql$)", re.I)),
    ("seeds", re.compile(r"(seed|seeder|fixture)", re.I)),
    ("menu_navigation", re.compile(r"(sidebar|navbar|menu|navigation|layout|nav\.)", re.I)),
    ("authorization", re.compile(r"(polic|guard|permission|permiso|ability|role|rol\.|auth)", re.I)),
]
RE_TESTS = dict(FILE_CATEGORIES)["tests"]
RE_ENV = re.compile(r"^\s*([A-Z][A-Z0-9_]{2,})\s*=", re.M)
INTEGRATION_HINTS = [
    "SMTP", "MAIL", "SENDGRID", "MAILGUN", "SES", "STRIPE", "PAYPAL", "TRANSBANK", "WEBPAY", "MERCADOPAGO",
    "AWS", "S3", "AZURE", "GCP", "GOOGLE", "FIREBASE", "TWILIO", "SLACK", "KEYCLOAK", "AUTH0", "OKTA",
    "LDAP", "SAML", "OAUTH", "REDIS", "RABBIT", "KAFKA", "SENTRY", "ELASTIC", "OPENAI", "WEBHOOK",
    "DOCUSIGN", "PUSHER", "ONESIGNAL", "FCM", "APNS", "SFTP", "FTP", "ERP", "SAP", "API_URL", "API_KEY",
]


def is_text(p: Path):
    name = p.name.lower()
    if name.startswith(".env") or name in {"dockerfile", "gemfile", "procfile"}:
        return True
    return p.suffix.lower() in TEXT_EXT


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root).as_posix()
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in EXCLUDED_DIRS and f"{rel}/{d}".lstrip("./") not in EXCLUDED_DIRS
            and not (d.startswith(".") and d not in {".github"})
        )
        for f in sorted(filenames):
            yield Path(dirpath) / f


def read(p: Path):
    try:
        if p.stat().st_size > MAX_SIZE:
            return None
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def normalize_route(r: str):
    r = r.split("?")[0].strip()
    r = re.sub(r"\$\{[^}]*\}", "{}", r)
    r = re.sub(r"<[^>]+>", "{}", r)
    r = re.sub(r"\{[^}]*\}", "{}", r)
    r = re.sub(r"(?<=/):\w+\??", "{}", r)
    r = re.sub(r"\(\?P<\w+>[^)]*\)", "{}", r)
    r = r.lstrip("^").rstrip("$")
    return ("/" + r.strip("/")).lower()


def detect_technologies(root, files):
    techs, manifests = set(), []
    for p in files:
        if p.name in MANIFESTS:
            manifests.append(p.relative_to(root).as_posix())
            techs.add(MANIFESTS[p.name])
            text = (read(p) or "").lower()
            for key, name in FRAMEWORKS:
                if re.search(r"['\"/:\s]" + re.escape(key.lower()) + r"(['\"\s/@=<>~^]|$)", text, re.M):
                    techs.add(name)
        elif p.suffix == ".csproj":
            manifests.append(p.relative_to(root).as_posix())
            techs.add(".NET")
            content = read(p) or ""
            if "Microsoft.AspNetCore" in content or "Sdk.Web" in content:
                techs.add("ASP.NET Core")
    return sorted(techs), manifests


def structure(root, files):
    per_dir = Counter()
    for p in files:
        parts = p.relative_to(root).parts
        if len(parts) > 1:
            per_dir["/".join(parts[:min(2, len(parts) - 1)])] += 1
        else:
            per_dir["(root)"] += 1
    return per_dir.most_common(60)


def main():  # noqa: C901
    setup_output()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--out", help="Output folder (default PROJECT/manual-docs/_work/reconnaissance)")
    ap.add_argument("--max-items", type=int, default=300, help="Maximum items per list in the report")
    args = ap.parse_args()

    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} does not exist", file=sys.stderr)
        return 2
    out = Path(args.out).resolve() if args.out else root / "manual-docs" / "_work" / "reconnaissance"
    out.mkdir(parents=True, exist_ok=True)

    files = [p for p in walk(root) if p.is_file()]
    texts = [p for p in files if is_text(p)]
    ext = Counter((p.suffix.lower() or p.name) for p in files)
    technologies, manifests = detect_technologies(root, files)

    routes, calls, auth = [], [], []
    roles = Counter()
    roles_where = defaultdict(set)
    role_enums = []
    categories = defaultdict(list)
    docs = []
    env_vars = set()

    for p in texts:
        rel = p.relative_to(root).as_posix()
        for cat, rx in FILE_CATEGORIES:
            if rx.search(rel):
                categories[cat].append(rel)
        if p.suffix.lower() in {".md", ".rst"} or "/docs/" in f"/{rel}":
            docs.append(rel)
        text = read(p)
        if text is None:
            continue
        if p.name.startswith(".env") or p.name.endswith(".example"):
            env_vars.update(RE_ENV.findall(text))
        if p.suffix.lower() in {".md", ".rst", ".txt", ".json", ".po", ".arb", ".resx", ".strings", ".lock"}:
            continue
        is_test = bool(RE_TESTS.search(rel))
        for n, line in enumerate(text.split("\n"), 1):
            if len(line) > 400:
                continue
            for label, layer, rx in ROUTE_PATTERNS:
                for m in rx.finditer(line):
                    path = m.group("path")
                    method = (m.groupdict().get("method") or "").upper()
                    if label == "Router (path: object)" and not (path.startswith("/") or path == "" or re.match(r"^[\w\-:]+(/[\w\-:]*)*$", path)):
                        continue
                    if (label == "Django" and p.suffix != ".py") or (label == "Rails" and p.suffix != ".rb") \
                            or (label == "Flutter" and p.suffix != ".dart"):
                        continue
                    routes.append({"layer": layer, "kind": label, "method": method, "path": path,
                                   "file": rel, "line": n, "in_test": is_test})
            if not is_test:
                for m in RE_HTTP_CALL.finditer(line):
                    met = next((g for g in (m.group("method"), m.group("m2"), m.group("m3"), m.group("m4")) if g), "")
                    calls.append({"method": met.upper(), "path": m.group("path"), "file": rel, "line": n})
            if AUTH_PATTERNS.search(line):
                auth.append({"file": rel, "line": n, "text": line.strip()[:200]})
            for rx in RE_ROLE_LITERALS:
                for m in rx.finditer(line):
                    val = m.group(1) if m.groups() else m.group(0)
                    for r in re.split(r"[|,\s\[\]]+", re.sub(r"['\"`]", "", val)):
                        r = r.strip()
                        if 2 <= len(r) <= 40 and re.match(r"^[A-Za-z][\w\-]*$", r):
                            roles[r] += 1
                            roles_where[r].add(rel)
            m = RE_ROLE_ENUM.search(line)
            if m:
                role_enums.append({"name": m.group(1), "file": rel, "line": n})

    # Backend routes with no apparent call from the interface
    call_paths = {normalize_route(c["path"]) for c in calls if c["path"]}

    def has_call(r):
        rn = normalize_route(r)
        return any(rn == c or rn.endswith(c) or c.endswith(rn) for c in call_paths if c != "/")

    backend = [r for r in routes if r["layer"] == "backend" and not r["in_test"]]
    no_caller = [r for r in backend if r["path"] and not has_call(r["path"])] if calls else []

    integrations = sorted(v for v in env_vars if any(k in v for k in INTEGRATION_HINTS))
    auth_files = Counter(a["file"] for a in auth)

    result = {
        "project": str(root),
        "total_files": len(files),
        "text_files": len(texts),
        "technologies": technologies,
        "manifests": manifests,
        "extensions": ext.most_common(30),
        "structure": structure(root, files),
        "routes": routes,
        "http_calls": calls,
        "backend_routes_without_apparent_caller": no_caller,
        "authorization": auth,
        "authorization_files": auth_files.most_common(),
        "candidate_roles": [{"value": k, "count": v, "files": sorted(roles_where[k])[:10]}
                            for k, v in roles.most_common()],
        "role_enums": role_enums,
        "categories": {k: sorted(set(v)) for k, v in categories.items()},
        "documentation": sorted(docs),
        "environment_variables": sorted(env_vars),
        "candidate_integrations": integrations,
    }
    (out / "reconnaissance.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    N = args.max_items
    L = []
    w = L.append
    w("# Project reconnaissance report\n")
    w("> Generated by scan_project.py. The results are **heuristic leads**: confirm each one in the code before recording it in `state.json`.\n")
    w(f"- Project: `{root}`")
    w(f"- Files analyzed: {len(files)} ({len(texts)} text)")
    w(f"- Technologies detected: {', '.join(technologies) or 'none recognized'}")
    w(f"- Manifests: {', '.join(f'`{m}`' for m in manifests) or '—'}\n")

    w("## Structure (files per folder, 2 levels)\n")
    w("| Folder | Files |\n|---|---|")
    for d, c in result["structure"]:
        w(f"| `{d}` | {c} |")
    w("\n## File types\n")
    w(", ".join(f"`{e}` {c}" for e, c in result["extensions"]) + "\n")

    for layer, title in (("interface", "Candidate interface routes"), ("backend", "Candidate backend routes")):
        items = [r for r in routes if r["layer"] == layer and not r["in_test"]]
        w(f"## {title} ({len(items)})\n")
        if items:
            w("| Kind | Method | Route | Location |\n|---|---|---|---|")
            for r in items[:N]:
                w(f"| {r['kind']} | {r['method'] or '—'} | `{r['path'] or '(empty)'}` | `{r['file']}:{r['line']}` |")
            if len(items) > N:
                w(f"\n… {len(items) - N} more in reconnaissance.json")
        else:
            w("None detected with the known patterns. Search manually (see patterns-by-technology.md).")
        w("")

    w(f"## HTTP calls from the frontend ({len(calls)})\n")
    if calls:
        w("| Method | URL | Location |\n|---|---|---|")
        for c in calls[:N]:
            w(f"| {c['method'] or '—'} | `{c['path']}` | `{c['file']}:{c['line']}` |")
    else:
        w("No calls detected with known patterns (the app may use generated clients or dynamic URLs).")
    w("")

    w(f"## Backend routes with no apparent call from the interface ({len(no_caller)})\n")
    w("Candidates for `backend-only`, integrations or dynamic calls. **Check each one** (see phase 2, section 5).\n")
    for r in no_caller[:N]:
        w(f"- {r['method'] or '—'} `{r['path']}` — `{r['file']}:{r['line']}`")
    w("")

    w("## Candidate roles and profiles\n")
    if role_enums:
        w("Definitions that look like role enums or classes:\n")
        for e in role_enums[:50]:
            w(f"- `{e['name']}` — `{e['file']}:{e['line']}`")
        w("")
    if roles:
        w("| Value | Count | Files (up to 3) |\n|---|---|---|")
        for r in result["candidate_roles"][:80]:
            w(f"| `{r['value']}` | {r['count']} | {', '.join(f'`{a}`' for a in r['files'][:3])} |")
    else:
        w("No role literals detected. Check ownership-based authorization, an external identity provider and seed data.")
    w("\nReminder: also check implicit profiles (phase 3, section 2).\n")

    w("## Files with authentication or authorization logic\n")
    w("| File | Matches |\n|---|---|")
    for a, c in result["authorization_files"][:N]:
        w(f"| `{a}` | {c} |")
    w("")

    category_titles = {
        "menu_navigation": "Menu and navigation", "authorization": "Authorization (by file name)",
        "validation": "Validation and forms", "translation": "Translations (literal interface texts)",
        "email_notification": "Email and notifications", "automatic_jobs": "Automatic jobs and queues",
        "models": "Models and entities", "migrations": "Migrations and schema", "seeds": "Seed data",
        "tests": "Automated tests",
    }
    for cat, title in category_titles.items():
        items = result["categories"].get(cat, [])
        w(f"## {title} ({len(items)})\n")
        for a in items[:min(N, 120)]:
            w(f"- `{a}`")
        if len(items) > 120:
            w(f"- … {len(items) - 120} more in reconnaissance.json")
        w("")

    w(f"## Existing documentation ({len(docs)})\n")
    for d in docs[:100]:
        w(f"- `{d}`")
    w("\n## Candidate integrations (environment variables)\n")
    w(", ".join(f"`{v}`" for v in integrations) or "None detected.")
    w("")
    (out / "reconnaissance.md").write_text("\n".join(L), encoding="utf-8")

    print(f"Technologies: {', '.join(technologies) or '—'}")
    print(f"Interface routes: {sum(1 for r in routes if r['layer'] == 'interface')} · Backend routes: {len(backend)} · "
          f"HTTP calls: {len(calls)} · No apparent caller: {len(no_caller)}")
    print(f"Candidate roles: {len(roles)} · Authorization files: {len(auth_files)}")
    print(f"Report: {out / 'reconnaissance.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
