# Task Completion Checklist

When you complete a coding task, follow these steps:

## 1. Code Quality
- [ ] Run Ruff linting: `ruff check .`
- [ ] Run Ruff formatting: `ruff format .`
- [ ] Fix any issues reported by Ruff

## 2. Type Checking
- [ ] Ensure all functions have type annotations
- [ ] Verify `TYPE_CHECKING` blocks for imports
- [ ] Check that `from __future__ import annotations` is present

## 3. Testing (if applicable)
- [ ] Test changes with Home Assistant: `hass -c config`
- [ ] Verify integration loads without errors
- [ ] Test uplight and downlight entities work independently
- [ ] Test the `lifx_ceiling.set_state` service if modified

## 4. Documentation
- [ ] Update docstrings if function signatures changed
- [ ] Update README.md if user-facing features changed
- [ ] Update CLAUDE.md if architecture changed significantly

## 5. Git Workflow
- [ ] Stage changes: `git add <files>`
- [ ] Commit with descriptive message: `git commit --no-gpg-sign -m "description"`
- [ ] Ensure commit message follows conventional commits format if applicable

## 6. Pre-Push Validation
- [ ] Ensure no linting errors remain
- [ ] Verify formatting is consistent
- [ ] Check that no debugging code (print statements, etc.) is left in

## Notes
- CI/CD runs automatically on push to main or PR
- GitHub Actions will run hassfest and HACS validation
- Linting workflow must pass before merge
