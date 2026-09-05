# Deploying the public demo on Hugging Face Spaces

The public demo runs the **deterministic engine** behind a "public sandbox"
banner. Assessment submissions are stateless: they are classified and returned
to that browser but are never added to a shared inventory. It deploys from the
repo's existing `Dockerfile` — no code changes per deploy.

> The demo is a public, multi-visitor sandbox. Use synthetic data only: input
> still crosses the public network and, when the Anthropic provider is enabled,
> is sent to that provider for drafting. `DEMO_MODE=1` prevents submitted
> assessments from entering shared storage; only shipped examples are listed.

## Demo-mode runtime settings

| Variable | Value | Why |
|---|---|---|
| `DEMO_MODE` | `1` | Shows the sandbox banner. |
| `LLM_PROVIDER` | `replay` | Pre-recorded drafts from the shipped examples (no model, no keys, no egress) so the AI-assist flow is visible. `none` hides the AI panel; with `DEMO_MODE=1`, `none` falls back to `replay` anyway. |
| `AIACT_DATA_DIR` | `/tmp/data` | Ephemeral provider-budget state; visitor assessments are not persisted. |
| `PORT` | `8000` (default) | Optional override. Keep the Space card's `app_port` equal to the port the container serves. |

### Optional: live AI drafts (`LLM_PROVIDER=anthropic`)

Instead of `replay`, set `LLM_PROVIDER=anthropic` to let the demo call the
real Claude API for prefill/narrative drafts, capped by a small spend guard
(see `README.md` → *AI layer (optional)*). This needs one **secret** and,
optionally, three **variables**:

| Name | Type | Value | Why |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **secret** | your API key | Never set this as a plain variable — Space *variables* are visible to anyone who can view the Space; *secrets* are not. Also set a spend limit on this key in the Anthropic Console as the hard guarantee. |
| `ANTHROPIC_WORKSPACE_ID` | `wrkspc_…` | Only for identity-linked keys (the API answers 400 "anthropic-workspace-id is required" otherwise). A variable, not a secret. |
| `AI_COOLDOWN_SECONDS` | `20` | Per-client cooldown; repeats of the same description are cached for an hour. |
| `AI_BUDGET_USD` | variable | `4.00` (default) | Lifetime USD spend cap; the app degrades to `replay` once it's hit. |
| `AI_DAILY_CALLS` | variable | `25` (default) | Daily call cap, independent of the budget. |
| `AI_CALLS_PER_IP_DAY` | variable | `8` (default) | Per-visitor daily call cap. |

`ANTHROPIC_MODEL` (default `claude-haiku-4-5`) can also be set as a variable
to change the model. All four cap/model variables are optional — omit them to
keep the defaults above.

Locally, you can preview the exact demo experience with:

```bash
DEMO_MODE=1 LLM_PROVIDER=none AIACT_DATA_DIR=/tmp/aiact-demo \
  uvicorn app.main:app --port 8000
# or, against the container:
docker build -t ai-act-companion .
docker run --rm -p 8000:8000 -e DEMO_MODE=1 -e LLM_PROVIDER=replay \
  -e AIACT_DATA_DIR=/tmp/data ai-act-companion
```

## Steps (you run these — they need your Hugging Face login)

GitHub merges do **not** deploy the Space. After every release, publish the
same source to the Space using the steps below; the private Sites review URL
is a separate deployment. Keep the live-demo link in the GitHub README and
the workspace About page pointed at the public Space.

For the 1.0 workspace, verify `/api/health` reports the intended version,
`/` opens `/static/workspace/index.html`, and `/api/workspace/catalogue`
contains three dossiers, nine reference profiles and 21 reports. Check that
the served `hub.js`, `hub.css` and `assets/about-context.png` match the release
files. The public sandbox notice must remain visible. A GitHub merge or a
successful private preview alone is not evidence that the public demo updated.

1. **Create the Space.** On <https://huggingface.co/new-space>: pick a name (e.g.
   `ai-act-companion`), **SDK = Docker** (blank template), visibility **Public**.
2. **Set the variables.** Space → *Settings* → *Variables and secrets* → add the
   three **variables** (not secrets) from the table above: `DEMO_MODE=1`,
   `LLM_PROVIDER=replay`, `AIACT_DATA_DIR=/tmp/data`. The checked-in Space card
   and Docker default both use port 8000; only set `PORT` if you update
   `app_port` to the same value.
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
   git fetch origin main
   GIT_LFS_SKIP_SMUDGE=1 git -c protocol.version=1 fetch space
   GIT_LFS_SKIP_SMUDGE=1 git worktree add ../space-deploy space/main
   cd ../space-deploy
   git checkout origin/main -- app static examples tests skills mcp_server.py \
       pyproject.toml requirements.txt action.yml CHANGELOG.md Dockerfile
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
   Confirm the sandbox banner shows, the labelled replay AI flow is available,
   a synthetic classification + reports render end-to-end, and a submitted
   assessment does not appear in the inventory after a refresh.
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
app_port: 8000
pinned: false
license: mit
short_description: Local-first, explainable EU AI Act risk classifier (demo).
---

# AI Act Companion — public demo

A public sandbox of [AI Act Companion](https://github.com/JKasteele/ai-act-companion):
a local-first, explainable EU AI Act risk classifier with an AI-security lens.
This demo runs the deterministic engine with stateless assessment submissions
and a labelled replay drafting assistant — **synthetic/example data only**.
```
