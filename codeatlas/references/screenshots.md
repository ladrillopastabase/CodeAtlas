# Screenshots

## Principle

Screenshots may only come from the real application while it runs. Never
generate, draw or present mockups or made-up images as if they were the
application. A mockup may be used only if it is explicitly captioned
"Illustration, not the real screen", and in general it is better not to use
one.

## When there is a running instance

1. Confirm the URL and environment with the user (prefer development or
   testing, never production with real people's data).
2. Use test accounts for each role, taken from the project's seed data or
   provided by the user. Do not create accounts in external services or use
   real third-party credentials.
3. Use fictional data in forms.
4. Capture with an available browser tool (browser extension, built-in
   browser or a Playwright/Puppeteer script against the local development
   environment).
5. Save in `manual-docs/screenshots/` named `P-xxx-description.png` (for
   example, `P-003-new-request-form.png`).
6. Recommended width: 1280–1440 px on desktop; crop to the relevant area when
   the screen is very large.
7. Mark elements with numbers or boxes when it helps. If the image cannot be
   edited, describe it in the text: "(1) **Description** field, (2) **Submit
   request** button".
8. Hide or blur any visible personal data.
9. Insert in the Markdown with descriptive alt text:

   ```markdown
   ![New request form with the Description and Estimated amount fields](../screenshots/P-003-new-request-form.png)
   *Figure 3. New request form.*
   ```

10. Record in the log the application version captured. If the code changes,
    the affected screenshots must be retaken.

## When there is no running instance

Leave a callout wherever a screenshot would help:

```markdown
> [!SCREENSHOT PENDING]
> **New request** screen (P-003) with the full form. Highlight:
> (1) **Description**, (2) **Estimated amount**, (3) **Submit request**.
```

Recommended minimum: sign-in screen, main screen after signing in (per role),
every creation form, every list with filters, every confirmation dialog for
irreversible actions and every settings screen.

`validate_manuals.py` counts pending screenshot callouts and the final
delivery lists them.
