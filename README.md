# Asterics Speech (Piper)

Self-hosted text-to-speech helper for [Asterics AAC](https://github.com/asterics/Asterics-AAC). Runs the [Asterics AAC Helper](https://github.com/asterics/Asterics-AAC-Helper) speech API with a [Piper](https://github.com/rhasspy/piper) backend, packaged as a Docker image.

The AAC web app talks to this service over HTTP (default port `5555`) to synthesize speech locally without cloud TTS.

## Quick start

### Build locally (recommended)

```bash
docker compose up --build -d
```

### Pull prebuilt image

GitHub Actions publishes `ghcr.io/jubblin/asterics-speech:latest` when speech service files change on `main`/`master`. The image must exist in GHCR before `docker compose pull` works.

If pull fails with `manifest unknown` or `denied`, build locally (above) or fix GHCR access:

1. Open [your packages](https://github.com/Jubblin?tab=packages) → `asterics-speech` → **Package settings**
2. Under **Manage Actions access**, grant `Jubblin/Asterics-Speech` **Write** (or delete an orphaned package and re-run the publish workflow)
3. Set package visibility to **Public** if you want anonymous `docker pull`

```bash
docker compose pull
docker compose up -d
```

Verify the service is healthy:

```bash
curl http://localhost:5555/voices/
curl http://localhost:5555/version/
```

Point Asterics AAC at `http://<host>:5555` in speech settings.

## Architecture

```mermaid
flowchart LR
    AAC[Asterics AAC] -->|HTTP| API[Flask speech API]
    API --> SM[speechManager]
    SM --> PP[provider_piper_data]
    PP --> Piper[piper CLI]
    Piper --> Model[Piper ONNX model]
```

At build time, the image clones `Asterics-AAC-Helper` and copies its `speech/` module (Flask app, `speechManager`, caching utilities). This folder adds:

| File | Role |
|------|------|
| `VERSION` | Semantic version (single source of truth for releases) |
| `version.py` | Reads `VERSION` at runtime |
| `Dockerfile` | Image build: system deps, helper code, Piper model, Python packages |
| `docker-compose.yml` | Local deployment with UK English voice defaults |
| `config.py` | Registers the Piper provider and enables response caching |
| `provider_piper_data.py` | Piper TTS provider implementation |
| `speech_logging.py` | Request, cache, and synthesis timing logs |
| `start_server.py` | Entrypoint; logging, `/version/`, binds host/port from env |

## API

Provided by Asterics AAC Helper (not defined in this folder):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/version/` | GET | Service version from `VERSION` (JSON `{"version":"…"}`) |
| `/voices/` | GET | List available voices (also used for health checks) |
| `/speakdata/<text>/` | GET/POST | Return synthesized audio (`application/octet-stream`) |
| `/speakdata/<text>/<providerId>/<voiceId>/` | GET/POST | Synthesize with explicit provider/voice |
| `/speaking/` | GET | Whether speech is in progress |
| `/stop/` | GET/POST | Stop playback |

Text in URLs is lowercased by the helper. With caching enabled, repeated phrases are served from `/app/speech/temp`.

## Configuration

### Runtime environment

| Variable | Default (compose) | Description |
|----------|-------------------|-------------|
| `SPEECH_HOST` | `0.0.0.0` | Bind address |
| `SPEECH_PORT` | `5555` | Listen port |
| `SPEECH_LOG_LEVEL` | `INFO` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `SPEECH_LOG_TEXT` | `false` | Log full spoken phrases at `INFO`; default logs `hash=` + `len=` only |
| `CACHE_DATA` | `true` | Cache synthesized audio on disk |
| `PIPER_SYNTH_TIMEOUT_SECONDS` | `60` | Max seconds to wait for Piper synthesis per request |
| `PIPER_PROVIDER_ID` | `piper_data` | Provider ID exposed to the AAC app |
| `PIPER_MODEL` | `/models/en_GB-alan-medium.onnx` | Path to ONNX model inside the container |
| `PIPER_VOICE_ID` | `en_GB-alan-medium` | Voice identifier |
| `PIPER_VOICE_NAME` | `UK English (Alan)` | Display name |
| `PIPER_VOICE_LANG` | `en-GB` | BCP 47 language tag |

### Build arguments (Dockerfile)

| Argument | Description |
|----------|-------------|
| `AAC_HELPER_COMMIT` | Git commit of [Asterics-AAC-Helper](https://github.com/asterics/Asterics-AAC-Helper) to vendor into the image |
| `VERSION` | Semantic version baked into OCI labels (defaults to `dev` for local builds; CI passes `VERSION` file) |
| `PIPER_MODEL_BASENAME` | Filename stem for the downloaded model |
| `PIPER_MODEL_ONNX_URL` | URL of the `.onnx` voice file |
| `PIPER_MODEL_JSON_URL` | URL of the matching `.onnx.json` config |

### Changing voice

1. Pick a voice from [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) (`.onnx` + `.onnx.json`).
2. Update `build.args` and matching `PIPER_*` environment variables in `docker-compose.yml`.
3. Rebuild: `docker compose up --build -d`.

Example alternative noted in `docker-compose.yml`: `en_GB-southern_english_female-medium`.

## Provider implementation

`provider_piper_data.py` implements the speech provider contract expected by `speechManager` in Asterics AAC Helper:

- `getProviderId`, `getVoiceType`, `getVoices`, `getSpeakData`

Functions are written in `snake_case` for lint compliance. CamelCase aliases (e.g. `getProviderId = get_provider_id`) are kept because the helper looks up those exact names at runtime.

`get_speak_data` invokes the `piper` CLI, writes output to a temp file via the helper's `util` module, and returns raw audio bytes. The `_voice_id` parameter is unused (single voice per container) but retained for API compatibility.

`constants` and `util` are supplied by the helper code copied into the image at build time, not by this repository.

## Logging

Structured logs go to stdout (view with `docker compose logs -f speech`).

| Layer | What is logged |
|-------|------------------|
| HTTP requests | Method, path, endpoint, text hash/length (or full text at `DEBUG` / `SPEECH_LOG_TEXT=true`), provider/voice, status, `elapsed_ms` |
| Cache | `cache=HIT` with `elapsed_ms`, or `cache=MISS` with `synth_ms` and `total_ms` |
| Piper | Synthesis duration and output size per phrase |

Example (default redaction at `INFO`):

```
request GET /speakdata/hello/ endpoint=speakdata text=hash=a665a4592042 len=5 ... elapsed_ms=820.1
speak cache=MISS synthesis=OK text=hash=a665a4592042 len=5 ... synth_ms=815.2 total_ms=821.4
piper synthesized text=hash=a665a4592042 len=5 bytes=12345 elapsed_ms=815.2

request GET /speakdata/hello/ ... elapsed_ms=3.1
speak cache=HIT text=hash=a665a4592042 len=5 ... elapsed_ms=2.4
```

Set `SPEECH_LOG_LEVEL=DEBUG` or `SPEECH_LOG_TEXT=true` in `docker-compose.yml` to log full spoken text.

## Versioning

The canonical version lives in [`VERSION`](VERSION) (currently `0.1.0`). CI reads this file and tags images accordingly.

| Image tag | When published |
|-----------|----------------|
| `latest` | Default branch (`main`/`master`) |
| `0.1.0` | Every publish (from `VERSION`) |
| `0.1`, `0` | Git tag push matching `v0.1.0` (semver) |
| `main`, `<sha>` | Branch and commit tags |

### Release a new version

1. Bump the version in `VERSION` (semver, no `v` prefix in the file).
2. Commit and push to `main`.
3. Tag and push (tag must match `VERSION` with a `v` prefix):

```bash
VERSION=$(tr -d ' \n\r\t' < VERSION)
git tag "v${VERSION}"
git push origin "v${VERSION}"
```

4. CI publishes `ghcr.io/jubblin/asterics-speech:${VERSION}`, semver aliases, and `latest`.

Pin deployments in `docker-compose.yml`:

```yaml
image: ghcr.io/jubblin/asterics-speech:0.1.0
```

## CI publish

Workflow: [`.github/workflows/publish-asterics-speech.yml`](.github/workflows/publish-asterics-speech.yml)

- **Trigger:** push to `master` or `main`, git tag `v*`, or manual **workflow_dispatch**; pull requests build only (no push)
- **Registry:** [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- **Image:** `ghcr.io/jubblin/asterics-speech` with tags `latest`, `VERSION`, semver aliases (on `v*` tags), branch name, and commit SHA

After the first publish, set the package visibility to **Public** under the repo’s **Packages** tab if you want anonymous `docker pull` (org default is often private).

## Image hardening

The Dockerfile follows container linting best practices:

- **Pinned apt packages** — `espeak-ng`, `git`, `ca-certificates`, `curl` use version patterns for reproducible Debian bookworm installs.
- **Pinned pip packages** — `flask`, `flask-cors`, `piper-tts` use exact versions.
- **HEALTHCHECK** — probes `http://127.0.0.1:5555/voices/` every 30s (15s start period) so orchestrators can detect a running but unresponsive container.

### Build args required

The Dockerfile downloads the Piper model at build time. Pass build args via `docker compose build` or explicitly:

```bash
docker build -f Dockerfile . \
  --build-arg PIPER_MODEL_BASENAME=en_GB-alan-medium \
  --build-arg PIPER_MODEL_ONNX_URL=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx \
  --build-arg PIPER_MODEL_JSON_URL=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json
```

Plain `docker build` without these args fails at the model download step.

## Quality checks

From the repo root (see also `CLAUDE.md` **Health Stack**):

```bash
# Docker image lint
hadolint Dockerfile
checkov -f Dockerfile

# Python syntax
python3 -m py_compile *.py
```

Known checkov finding: `CKV_DOCKER_3` (container runs as root). Acceptable for local/LAN use; add a non-root `USER` before production hardening.

Run `/health` (gstack) for a scored dashboard and trend tracking.

## Volumes

- `piper-cache` (compose) → `/app/speech/temp` — persisted TTS cache across restarts.
