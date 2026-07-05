# Asterics Speech

## Health Stack

Commands used by `/health` and local quality checks for this repo:

- lint-docker: hadolint Dockerfile
- lint-container: checkov -f Dockerfile
- lint-python: python3 -m py_compile *.py

Notes:

- Typecheck (`tsc`) is not applicable — no `tsconfig.json`.
- `npm test` and `shellcheck` are not applicable — no Node app or shell scripts in this repo.
- `knip` and `gbrain` are optional; skipped when not installed.
