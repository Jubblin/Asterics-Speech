# Asterics AAC

## Health Stack

Commands used by `/health` and local quality checks for this repo:

- test: npm test
- lint-docker: hadolint deploy/asterics-speech/Dockerfile
- lint-container: checkov -f deploy/asterics-speech/Dockerfile
- lint-python: python3 -m py_compile deploy/asterics-speech/*.py
- shell: shellcheck scripts/*.sh

Notes:

- Typecheck (`tsc`) is not applicable — no `tsconfig.json`.
- Run `npm install` before `npm test` if `node_modules` is missing.
- `knip` and `gbrain` are optional; skipped when not installed.
