# Contributing to ZapUnlocked-API

All contributions are welcome, whether a bug report, feature suggestion, or pull request.

---

## Report a Problem

Before opening an issue, check if it already exists in [open issues](https://github.com/kauafpssx/ZapUnlocked-API/issues).

- **Bug**: use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template
- **Feature**: use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template

Issues without enough context may be closed.

---

## Contribute Code

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USER/ZapUnlocked-API.git
cd ZapUnlocked-API
```

### 2. Create a branch

```bash
git checkout -b feat/feature-name
# or
git checkout -b fix/bug-name
```

### 3. Implement

Keep the scope focused. One PR per feature or fix.

### 4. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add location sending endpoint
fix: fix timeout in media queue
docs: update webhook examples
refactor: extract auth logic to separate module
chore: update dependencies
```

### 5. Open the Pull Request

PR to the `main` branch, filling out the template completely.

---

## Standards

- Python: PEP 8, descriptive English names
- No debug `print()` in PRs
- No commented-out code left behind
- Imports: stdlib, third-party, local (in that order)

---

## Security

Never open a public issue for vulnerabilities. See [SECURITY.md](SECURITY.md).