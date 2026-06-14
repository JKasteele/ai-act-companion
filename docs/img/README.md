# Screenshots

The main `README.md` embeds these screenshots of the running app:

| File | View |
|---|---|
| `result.png` | Classification result (after "Load example" → "Classify & generate") |
| `security.png` | The AI security lens (OWASP LLM Top 10 + MITRE ATLAS) |
| `report.png` | Rendered report preview (Risk assessment tab) |
| `ai-assist.png` | The AI assist panel (free-text → human-in-the-loop draft) |

They are real captures of the live UI (no mock-ups). To regenerate, run the app
(`uvicorn app.main:app`) and use a headless-browser capture against
`http://127.0.0.1:8000`.
