# Use inside GitHub Copilot

AI Act Companion already ships as a [Claude Code plugin](../README.md#use-inside-claude-code)
(MCP server + skill). The **same deterministic engine** also works with **GitHub
Copilot** — the coding agent, **Copilot Cowork**, VS Code agent mode and the
Copilot CLI — because they all speak the **Model Context Protocol (MCP)** and all
read the same custom-instructions file.

As everywhere else: **the risk tier and citations come only from the engine** —
Copilot is the interface and narrative author, and human-in-the-loop review is
mandatory. See [`DESIGN.md`](../DESIGN.md) for why.

## What's in the repo for Copilot

| File | What Copilot does with it |
|---|---|
| [`.github/copilot-instructions.md`](../.github/copilot-instructions.md) | Repo-wide custom instructions (the Copilot counterpart of `CLAUDE.md`). Loaded automatically by the coding agent, Cowork and VS Code agent mode. |
| [`.github/prompts/ai-act-assessment.prompt.md`](../.github/prompts/ai-act-assessment.prompt.md) | The human-in-the-loop assessment playbook as a reusable **prompt file** (the Copilot counterpart of the Claude skill). |
| [`.vscode/mcp.json`](../.vscode/mcp.json) | Registers the `ai-act-companion` MCP server for **VS Code** agent mode (loads on open). |
| [`.github/workflows/copilot-setup-steps.yml`](../.github/workflows/copilot-setup-steps.yml) | Pre-installs the engine + MCP deps in the **cloud agent** (coding agent / Cowork) environment. |

First install the MCP dependency locally (and for the CLI/web paths):

```bash
pip install -e ".[mcp]"
```

## VS Code (agent mode) — local

1. Open the repo in VS Code with GitHub Copilot.
2. `.vscode/mcp.json` registers the server automatically; **Start** it when
   prompted (or run **MCP: List Servers**). It launches `python mcp_server.py`,
   so the `python` on your PATH must have `pip install -e ".[mcp]"`.
3. In the Copilot Chat **Agent** mode, enable the `ai-act-companion` tools, then
   run the prompt file: type `/ai-act-assessment`, or just describe a system —
   e.g. *"Run an EU AI Act assessment for my CV-screening system."*

## Copilot coding agent & Cowork (cloud) — per repository

The cloud agents don't read a committed MCP file; you register the server **once
in repository settings**:

1. **Settings → Copilot → Coding agent → MCP configuration** (the same MCP config
   is used by Cowork when it operates on this repo).
2. Paste:

   ```json
   {
     "mcpServers": {
       "ai-act-companion": {
         "type": "stdio",
         "command": "python",
         "args": ["mcp_server.py"],
         "tools": ["*"]
       }
     }
   }
   ```

3. Save. `copilot-setup-steps.yml` installs `pip install -e ".[dev,mcp]"` in the
   agent's ephemeral environment first, so `python mcp_server.py` resolves from
   the repo root. The agent then has `classify_ai_system`, `generate_report`, …
   available, governed by `.github/copilot-instructions.md`.

> The coding agent runs with the repo root as its working directory, so the
> relative `mcp_server.py` path is correct and portable — the same reason
> `.mcp.json` uses a relative path.

## Copilot CLI — local

```bash
copilot                                    # start the CLI in this repo
# then register the local server:
/mcp add ai-act-companion --command python --args mcp_server.py
```

(Or add it to the CLI's MCP config file.) Custom instructions and prompt files in
`.github/` are picked up automatically.

## Standard (GPT-based) Copilot completions

Inline code completion and Chat don't run MCP tools, but they **do** read
`.github/copilot-instructions.md`, so suggestions still respect the one invariant
(the engine decides the tier; the AI never does) and the project conventions. For
the full assessment workflow, use one of the agent surfaces above.

## Provenance

- *Copilot Cowork* is Microsoft 365 Copilot's cloud agent (general availability
  June 2026). It uses the repository's MCP configuration and
  `.github/copilot-instructions.md` when operating on a repo, the same as the
  GitHub Copilot coding agent.
- The MCP config schema and the `copilot-setup-steps.yml` job name
  (`copilot-setup-steps`) follow current GitHub Docs.
