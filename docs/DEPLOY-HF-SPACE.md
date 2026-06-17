# Deploying the public demo on Hugging Face Spaces

The public demo runs the **deterministic engine** with the optional AI layer off
and ephemeral storage, behind a "public sandbox" banner. It deploys from the
repo's existing `Dockerfile` — no code changes per deploy.

> The demo is a public, multi-visitor sandbox: it stores synthetic assessments in
> ephemeral storage shared across visitors. That is acceptable **only** with
> `DEMO_MODE=1` (banner + synthetic-data-only guidance). Do not point a public
> Space at persistent storage — multi-user isolation is out of scope by design
> (see `DESIGN.md` / `SECURITY.md`).

## Demo-mode runtime settings

| Variable | Value | Why |
|---|---|---|
| `DEMO_MODE` | `1` | Shows the sandbox banner. |
| `LLM_PROVIDER` | `none` | No AI layer, no API keys, no egress. |
| `AIACT_DATA_DIR` | `/tmp/data` | Ephemeral storage; reset on rebuild/restart. |
| `PORT` | `7860` | HF Spaces injects this; the Dockerfile honours `$PORT`. |

Locally, you can preview the exact demo experience with:

```bash
DEMO_MODE=1 LLM_PROVIDER=none AIACT_DATA_DIR=/tmp/aiact-demo \
  uvicorn app.main:app --port 8000
# or, against the container:
docker build -t ai-act-companion .
docker run --rm -p 7860:7860 -e DEMO_MODE=1 -e LLM_PROVIDER=none \
  -e AIACT_DATA_DIR=/tmp/data -e PORT=7860 ai-act-companion
```

## Steps (you run these — they need your Hugging Face login)

1. **Create the Space.** On <https://huggingface.co/new-space>: pick a name (e.g.
   `ai-act-companion`), **SDK = Docker** (blank template), visibility **Public**.
2. **Set the variables.** Space → *Settings* → *Variables and secrets* → add the
   three **variables** (not secrets) from the table above: `DEMO_MODE=1`,
   `LLM_PROVIDER=none`, `AIACT_DATA_DIR=/tmp/data`. (HF sets `PORT` itself.)
3. **Add the Space card.** A Docker Space needs `app_port` in the README front
   matter. In the Space's web editor, create/replace its `README.md` with the
   header in [the Space card](#space-card-readmemd-front-matter) below. Keep this
   as the **Space's** README — do not copy it into the GitHub repo README.
4. **Push the code.** From a clone of this repo:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-hf-username>/ai-act-companion
   git push space main
   ```
   (Use an HF access token with *write* scope when prompted for a password, or
   run `huggingface-cli login` first. In Claude Code you can run the login
   interactively by typing `! huggingface-cli login`.)
5. **Wait for the build**, then open `https://huggingface.co/spaces/<your-hf-username>/ai-act-companion`.
   Confirm the sandbox banner shows, the AI panel is hidden, and a synthetic
   classification + reports render end-to-end.
6. **Link it from the README.** Once the URL is live, add the live-demo badge to
   the top of `README.md` (see the project TODO in the release notes).

## Space card (`README.md` front matter)

```yaml
---
title: AI Act Companion
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Local-first, explainable EU AI Act risk classifier (demo).
---

# AI Act Companion — public demo

A public sandbox of [AI Act Companion](https://github.com/JKasteele/ai-act-companion):
a local-first, explainable EU AI Act risk classifier with an AI-security lens.
This demo runs the deterministic engine with the AI layer **off** and ephemeral
storage — **synthetic/example data only**.
```
