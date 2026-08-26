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
4. **Push the code.** The Space repo keeps its **own git history** — its
   `README.md` is the Space card (step 3) and `docs/img/*` are LFS stubs — so
   do **not** push GitHub `main` over it. Layer a deploy commit on top of the
   Space branch instead:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-hf-username>/ai-act-companion
   GIT_LFS_SKIP_SMUDGE=1 git -c protocol.version=1 fetch space
   GIT_LFS_SKIP_SMUDGE=1 git worktree add ../space-deploy space/main
   cd ../space-deploy
   git checkout main -- app static examples tests skills mcp_server.py \
       pyproject.toml action.yml CHANGELOG.md Dockerfile
   git commit -m "Deploy vX.Y.Z (<what changed>)"
   git -c protocol.version=1 push space HEAD:main
   cd - && git worktree remove ../space-deploy
   ```
   Notes: `protocol.version=1` works around a protocol-v2 handshake error with
   the HF git server ("expected 'acknowledgments'"); `GIT_LFS_SKIP_SMUDGE=1`
   leaves the Space's LFS image stubs untouched (their objects live on HF, not
   GitHub). Authenticate with your HF username + a *write*-scope access token
   as the git password (`huggingface-cli login` / `hf auth login` stores one at
   `~/.cache/huggingface/token`). In Claude Code you can run the login
   interactively by typing `! hf auth login`.
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
