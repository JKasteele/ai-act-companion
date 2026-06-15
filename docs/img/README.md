# Screenshots

The main `README.md` embeds these captures of the running app:

| File | View |
|---|---|
| `demo.gif` | Hero animation: classify → architecture-aware severity → red-team test plan → framework matrix |
| `result.png` | Classification result (high-risk example: tier, findings, obligations) |
| `security.png` | AI security lens — architecture-aware severity (OWASP LLM Top 10 + MITRE ATLAS) |
| `redteam.png` | Red-team test plan — priority summary + a Critical, architecture-aware test case |
| `report.png` | Obligations & conformity tracker with the Art. 99 penalty block |
| `framework-matrix.png` | NIST CSF 2.0 / ISO 27001:2022 framework integration matrix |
| `ai-assist.png` | The AI assist panel (free-text → human-in-the-loop draft) |
| `inventory.png` | The AI system inventory dashboard |

They are real captures of the live UI (no mock-ups). To regenerate, run the app
and the capture script:

```bash
uvicorn app.main:app --port 8000        # one terminal
python scripts/capture_demo.py           # another (writes the files here)
```

The script (`scripts/capture_demo.py`) drives the same UI a user would — load an
example from the dropdown, classify, click through the report tabs — using a
headless browser. Requires `pip install -e ".[dev,capture]" && playwright install chromium`.
