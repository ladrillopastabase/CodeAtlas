# Where to look in each technology

A locator guide. For each stack: interface routes, backend routes,
authorization and roles, validations, visible messages, states, automatic
processes. If the project mixes technologies, apply each section and connect
the layers through the HTTP calls (URL and method).

## Contents

- Frontend: React / Next.js, Vue / Nuxt, Angular, server-rendered templates
- Backend: Node (Express, NestJS), Python (Django, Flask, FastAPI), PHP
  (Laravel), Java (Spring), .NET, Ruby on Rails, Go
- Mobile: Flutter, React Native, Android, iOS
- Cross-cutting: translations, email, jobs, flags, configuration

## Frontend

### React / Next.js
- Routes: `react-router` (`<Route path=`, `createBrowserRouter`, `path:`),
  Next.js `pages/` or `app/` (each `page.tsx` is a screen; `[id]` is a
  parameter; `layout.tsx` holds navigation).
- Menu: `Sidebar`, `Nav`, `Menu`, `Layout` components; configuration arrays
  with `label`, `path`, `icon`, `roles`.
- Protection: `PrivateRoute`, `RequireAuth`, `ProtectedRoute` components,
  `middleware.ts` (Next), `useAuth`, `usePermission`, `can(` hooks.
- Forms: `react-hook-form` (`register(`, `rules`), `formik`, `yup`/`zod`
  schemas (`.required(`, `.min(`, `.email(`, messages).
- Calls: `fetch(`, `axios.`, `api/` services, `useQuery`, `useMutation`.
- Messages: `toast.`, `notification.`, `alert(`, `enqueueSnackbar`,
  confirmation dialogs (`confirm(`, `Modal`, `Dialog`).

### Vue / Nuxt
- Routes: `router/index.(js|ts)` with `path`, `name`, `meta: { roles,
  requiresAuth }`; Nuxt `pages/`.
- Guards: `router.beforeEach`, `middleware/`.
- Forms: `v-model`, `vee-validate`, `vuelidate`, `rules`.
- Conditional visibility: `v-if="can(..."`, `v-if="user.role ==="`.
- Messages: `$toast`, `ElMessage`, `$q.notify`, `i18n/` files.

### Angular
- Routes: `*-routing.module.ts` or `app.routes.ts` (`path`, `component`,
  `canActivate`, `data: { roles }`).
- Guards: `*.guard.ts`. Custom permission directives (`*hasRole`,
  `*ngIf="auth.has...`).
- Forms: `FormBuilder`, `Validators.required`, `Validators.pattern`.
- Messages: `MatSnackBar`, `ToastrService`, `translate` pipe and
  `assets/i18n/*.json`.

### Server-rendered templates
- Django templates, Blade (Laravel), Thymeleaf, Razor, ERB, Jinja: look for
  `{% if perms.`, `@can`, `@role`, `sec:authorize`, `User.IsInRole`,
  `<% if can? %>`. Forms and buttons are in the templates themselves.

## Backend

### Node: Express / Fastify / Koa
- Routes: `app.get(`, `router.post(`, `fastify.route(`.
- Authorization: middlewares in the route chain (`auth`, `isAdmin`,
  `checkRole(`, `authorize(`), libraries `casl`, `accesscontrol`.
- Validation: `express-validator`, `joi`, `celebrate`, `zod`.
- Error responses: `res.status(4xx).json({ message:`.

### NestJS
- Controllers: `@Controller(`, `@Get(`, `@Post(`.
- Roles: `@Roles(`, `@UseGuards(`, `RolesGuard`, `Role` enums.
- Validation: DTOs with `class-validator` (`@IsNotEmpty`, `@MaxLength`).
- Exceptions: `throw new ForbiddenException('...')`, `BadRequestException`.

### Django / Django REST Framework
- Routes: `urls.py` (`path(`, `re_path(`, DRF routers).
- Views: `views.py`, `viewsets`. Permissions: `permission_classes`,
  `@login_required`, `@permission_required`, `has_perm`, `user.is_staff`,
  `is_superuser`, groups (`Group`), `Meta.permissions`.
- **The Django admin** (`admin.py`) is a real user interface for staff:
  document it if it is used operationally.
- Validation: `forms.py`, `serializers.py`, `clean_*`, `validators`.
- Models and states: `models.py`, `choices`, `TextChoices`.
- Messages: `messages.success(`, `ValidationError(`, `gettext`/`_(`,
  `locale/*.po`.
- Automatic: `celery` tasks, `signals.py`, `management/commands`.

### Flask / FastAPI
- Routes: `@app.route(`, `@bp.route(`, `@router.get(`.
- Authorization: decorators (`@login_required`, `@roles_required`),
  `Depends(get_current_user)` dependencies, scope checks.
- Validation: `WTForms`, `pydantic` (`Field(..., max_length=)`, validators).
- Errors: `abort(403)`, `HTTPException(status_code=, detail=)`.

### Laravel
- Routes: `routes/web.php`, `routes/api.php` (`Route::get(`,
  `->middleware('role:admin')`, `Route::resource`).
- Authorization: `app/Policies`, `Gate::define`, `$this->authorize(`,
  `@can`, packages such as `spatie/laravel-permission` (tables `roles`,
  `permissions`, seeders).
- Validation: `app/Http/Requests/*Request.php` (`rules()`, `messages()`),
  `$request->validate(`; texts in `lang/*/validation.php`.
- Automatic: `app/Console/Kernel.php` (schedule), `Jobs`, `Listeners`,
  `Notifications`, `Mail`.

### Spring (Java / Kotlin)
- Routes: `@RestController`, `@GetMapping`, `@RequestMapping`.
- Security: `SecurityFilterChain` / `WebSecurityConfigurerAdapter`
  (`hasRole`, `hasAuthority`, `permitAll`), `@PreAuthorize`, `@Secured`.
- Validation: `@NotNull`, `@Size`, `@Pattern`, `@Valid`,
  `messages.properties`.
- Automatic: `@Scheduled`, `@KafkaListener`, `@RabbitListener`.

### .NET
- Routes: controllers (`[Route]`, `[HttpGet]`), Razor Pages, minimal APIs
  (`app.MapGet`).
- Authorization: `[Authorize(Roles = "...")]`, `[Authorize(Policy =`,
  `AddAuthorization(options => options.AddPolicy(`.
- Validation: DataAnnotations (`[Required]`, `[StringLength]`),
  FluentValidation. `.resx` resources.
- Automatic: `IHostedService`, Hangfire, Quartz.

### Ruby on Rails
- Routes: `config/routes.rb` (`resources`, `namespace :admin`).
- Authorization: Pundit (`app/policies`), CanCanCan (`ability.rb`),
  `before_action :authenticate_user!`, Devise (sign-up, confirmation,
  account locking).
- Validation: `validates` in models; texts in `config/locales/*.yml`.
- States: `enum status:`, `aasm`, `state_machines` gems.
- Automatic: `app/jobs`, `sidekiq`, `whenever` (`schedule.rb`).

### Go
- Routes: `r.GET(`, `e.POST(`, `http.HandleFunc(`; authorization middlewares
  on the route group.
- Validation: `validate:"required,max=50"` tags.

## Mobile

- **Flutter**: routes in `MaterialApp(routes:` or `go_router`; screens in
  `lib/screens` or `lib/features`; validation in `validator:` on
  `TextFormField`; texts in `l10n/*.arb`.
- **React Native**: `@react-navigation` (`Stack.Screen name=`), forms as in
  React.
- **Android**: `AndroidManifest.xml` (activities), `res/navigation/*.xml`,
  `res/values*/strings.xml`.
- **iOS**: storyboards, SwiftUI `NavigationLink`, `Localizable.strings`.

Consider device permissions (camera, location, push notifications) and
offline behavior: they affect users and must be documented.

## Cross-cutting elements

| Element | Where to look | What it gives the manual |
|---|---|---|
| Translations | `i18n/`, `locales/`, `lang/`, `*.po`, `*.arb`, `*.resx`, `messages*.properties` | Literal button, field and message texts |
| Email and notifications | `mail/`, `emails/`, `notifications/`, templates | What the user receives and when |
| Scheduled jobs | cron, schedulers, workers, queues | Automatic processes that change states |
| Feature flags and configuration | `.env.example`, `config/`, settings tables | Features that may or may not be active per installation |
| Seed data | `seeders/`, `fixtures/`, `seeds.rb`, data migrations | Roles, permissions and initial catalogs |
| Tests | `tests/`, `spec/`, `e2e/`, `cypress/`, `playwright/`, `*.feature` | Real flows, expected messages and confirmed error cases |
| Exports and imports | `export`, `import`, `csv`, `xlsx`, `pdf` | Formats the user must follow |
