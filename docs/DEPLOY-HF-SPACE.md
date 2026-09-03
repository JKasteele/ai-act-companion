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
| `LLM_PROVIDER` | `replay` | Pre-recorded drafts from the shipped examples (no model, no keys, no egress) so the AI-assist flow is visible. `none` hides the AI panel; with `DEMO_MODE=1`, `none` falls back to `replay` anyway. |
| `AIACT_DATA_DIR` | `/tmp/data` | Ephemeral storage; reset on rebuild/restart. |
| `PORT` | `7860` | HF Spaces injects this; the Dockerfile honours `$PORT`. |

### Optional: live AI drafts (`LLM_PROVIDER=anthropic`)

Instead of `replay`, set `LLM_PROVIDER=anthropic` to let the demo call the
real Claude API for prefill/narrative drafts, capped by a small spend guard
(see `README.md` → *AI layer (optional)*). This needs one **secret** and,
optionally, three **variables**:

| Name | Type | Value | Why |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **secret** | your API key | Never set this as a plain variable — Space *variables* are visible to anyone who can view the Space; *secrets* are not. Also set a spend limit on this key in the Anthropic Console as the hard guarantee. |
| `ANTHROPIC_WORKSPACE_ID` | `wrkspc_…` | Only for identity-linked keys (the API answers 400 "anthropic-workspace-id is required" otherwise). A variable, not a secret. |
| `AI_BUDGET_USD` | variable | `5.00` (default) | Lifetime USD spend cap; the app degrades to `replay` once it's hit. |
| `AI_DAILY_CALLS` | variable | `40` (default) | Daily call cap, independent of the budget. |
| `AI_CALLS_PER_IP_DAY` | variable | `8` (default) | Per-visitor daily call cap. |

`ANTHROPIC_MODEL` (default `claude-sonnet-5`) can also be set as a variable
to change the model. All four cap/model variables are optional — omit them to
keep the defaults above.

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
6. **Link it from the README.** Once the URL is live, point the live-demo badge
   at the top of `README.md` at your Space (the canonical deployment already
   carries one).

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
