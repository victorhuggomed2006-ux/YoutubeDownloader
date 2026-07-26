<!--
Write in English, Portuguese or Spanish — whichever you are comfortable with.
-->

## What changed and why

<!--
The "why" matters more than the "what" — the diff already shows what changed.
-->

## How was it verified

<!--
Tests, manual steps, the video you tried it on.
-->

## Checklist

- [ ] `pytest` passes
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] New user-facing strings are wrapped in `tr()` and the `.ts` files were
      updated (`packaging/build_translations.ps1`)
- [ ] Business logic went into `core/` (no Qt imports there)
- [ ] `CHANGELOG.md` updated, if the change is user-visible
