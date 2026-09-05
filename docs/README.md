# Documentation

## Start here

- [Project overview](../README.md)
- [System workspace](WORKSPACE.md): full toolkit, browser engine, case, agent tools, limitations
- [Contributing](../CONTRIBUTING.md) and [shared assistant instructions](../AGENTS.md)

## Architecture and reference

- [Live evidence evaluation](EVIDENCE-EVALUATION.md): probes, human review and operational results
- [Engine design](DESIGN.md)
- [Threat model](THREAT_MODEL.md) and [security policy](../SECURITY.md)
- [Toolkit reference](TOOLKIT.md): original intake, CLI, reports, configuration
- [Copilot / MCP integration](COPILOT.md)
- [Hugging Face deployment](DEPLOY-HF-SPACE.md)
- [Generated example reports](examples/README.md)

## Earlier demo materials

These describe the original questionnaire, still available at `/classic`.

- [Demo script](DEMO-SCRIPT.md)
- [Screenshots](img/README.md)
- [Earlier roadmap review](ROADMAP-REVIEW.md)

Build workspace assets with `npm ci` then `python scripts/build_workspace.py`.
Verify the browser engine with `npm run test:engine`.
Build the original report gallery with `python scripts/build_gallery.py`.
