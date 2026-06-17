"""Repository AI-usage scanner.

Pure, stdlib-only `scan_repo(path) -> dict`. Walks a codebase and flags whether it
appears to use AI/ML (dependency manifests, source imports, model artifacts), then
points to the EU AI Act questions worth asking. It is a deterministic **relevance
flag, NOT a classification** — it never assigns a risk tier (only the questionnaire
+ classifier do that). Designed to run as a CI check / GitHub Action so an AI
system surfaces early.

No third-party dependencies, so it runs fast in a CI step.
"""

import re
from pathlib import Path

# library / import token -> (category, human note). category: "genai" (LLM /
# generative) or "ml" (classical / deep learning).
AI_LIBRARIES = {
    "openai": ("genai", "OpenAI LLM API"),
    "anthropic": ("genai", "Anthropic Claude API"),
    "google.generativeai": ("genai", "Google Gemini API"),
    "genai": ("genai", "Google GenAI SDK"),
    "cohere": ("genai", "Cohere LLM API"),
    "mistralai": ("genai", "Mistral LLM API"),
    "langchain": ("genai", "LLM orchestration (LangChain)"),
    "llama_index": ("genai", "RAG framework (LlamaIndex)"),
    "llama-index": ("genai", "RAG framework (LlamaIndex)"),
    "transformers": ("genai", "Hugging Face Transformers"),
    "sentence_transformers": ("genai", "embeddings (Sentence-Transformers)"),
    "huggingface_hub": ("genai", "Hugging Face Hub"),
    "ollama": ("genai", "local LLM runtime (Ollama)"),
    "vllm": ("genai", "LLM serving (vLLM)"),
    "torch": ("ml", "PyTorch deep-learning framework"),
    "tensorflow": ("ml", "TensorFlow deep-learning framework"),
    "keras": ("ml", "Keras deep-learning API"),
    "sklearn": ("ml", "scikit-learn classical ML"),
    "scikit-learn": ("ml", "scikit-learn classical ML"),
    "xgboost": ("ml", "gradient-boosted trees (XGBoost)"),
    "lightgbm": ("ml", "gradient-boosted trees (LightGBM)"),
    "onnxruntime": ("ml", "ONNX model runtime"),
    "spacy": ("ml", "NLP pipeline (spaCy)"),
}

_MODEL_EXTS = {".onnx", ".pt", ".pth", ".gguf", ".safetensors", ".h5",
               ".tflite", ".pb", ".ckpt", ".joblib"}
_MANIFESTS = {"requirements.txt", "requirements-dev.txt", "pyproject.toml",
              "setup.py", "setup.cfg", "Pipfile", "environment.yml",
              "package.json"}
_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "dist", "build",
              "__pycache__", ".mypy_cache", ".pytest_cache", "site-packages",
              ".next", "target", ".tox", "vendor"}
_SOURCE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".ipynb"}
_MAX_BYTES = 300_000   # don't read very large files
_MAX_FILES = 6000      # backstop on huge repos


def _token_in(text, token):
    return re.search(r"(?<![\w.-])" + re.escape(token) + r"(?![\w-])", text) is not None


def scan_repo(root="."):
    """Scan a repository tree for AI/ML usage. Returns a structured relevance flag."""
    root = Path(root)
    libs = {}            # name -> {"name","category","note","where":set}
    model_files = []
    scanned = 0
    truncated = False

    for path in sorted(root.rglob("*")):
        if scanned >= _MAX_FILES:
            truncated = True
            break
        if path.is_dir() or any(part in _SKIP_DIRS for part in path.parts):
            continue
        name, ext = path.name, path.suffix.lower()

        if ext in _MODEL_EXTS:
            model_files.append(str(path.relative_to(root)).replace("\\", "/"))
            continue
        is_manifest = name in _MANIFESTS
        if not is_manifest and ext not in _SOURCE_EXTS:
            continue
        try:
            if path.stat().st_size > _MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        where = "dependency" if is_manifest else "import"
        for token, (category, note) in AI_LIBRARIES.items():
            if _token_in(text, token):
                entry = libs.setdefault(token.replace("-", "_").split(".")[0],
                                        {"name": token, "category": category,
                                         "note": note, "where": set()})
                entry["where"].add(where)

    library_list = sorted(
        ({**v, "where": sorted(v["where"])} for v in libs.values()),
        key=lambda e: e["name"])
    categories = sorted({e["category"] for e in library_list})
    ai_detected = bool(library_list or model_files)
    has_genai = "genai" in categories

    if ai_detected:
        n = len(library_list) + (1 if model_files else 0)
        recommendation = (
            f"This repository appears to use AI/ML ({n} indicator(s)). If the system "
            "is placed on the EU market or affects persons in the EU (Art. 2), run an "
            "EU AI Act assessment — this scan is only a relevance flag, not a "
            "classification.")
    else:
        recommendation = (
            "No AI/ML indicators were found in the scanned files. If you nonetheless "
            "build, integrate or deploy AI, run an EU AI Act assessment.")

    considerations = []
    if ai_detected:
        considerations.append("Art. 2 — does it reach the EU market or affect persons in the EU?")
        considerations.append("Art. 5 — could any use be a prohibited practice "
                              "(e.g. social scoring, manipulation, untargeted scraping)?")
        considerations.append("Art. 6 + Annex III — is it used in a high-risk domain "
                              "(employment, credit, biometrics, education, essential "
                              "services, law enforcement, justice, migration)?")
        if has_genai:
            considerations.append("Art. 50 — generative/LLM use needs transparency "
                                  "(disclose AI interaction; mark synthetic content); "
                                  "review the AI-security lens (OWASP LLM Top 10).")
        if any("ml" == e["category"] for e in library_list) or model_files:
            considerations.append("Art. 10 — data governance for training/validation data.")

    return {
        "ai_detected": ai_detected,
        "libraries": library_list,
        "model_files": sorted(model_files)[:50],
        "model_file_count": len(model_files),
        "categories": categories,
        "scanned_files": scanned,
        "truncated": truncated,
        "recommendation": recommendation,
        "considerations": considerations,
    }


def format_report(result):
    """Render the scan result as Markdown (works in a terminal and as a CI summary)."""
    lines = ["## EU AI Act relevance scan", ""]
    if result["ai_detected"]:
        lines.append(f"**AI/ML usage detected.** {result['recommendation']}")
    else:
        lines.append(f"**No AI/ML indicators found.** {result['recommendation']}")
    lines.append("")
    if result["libraries"]:
        lines.append("| Library | Kind | Found in | Note |")
        lines.append("|---|---|---|---|")
        for e in result["libraries"]:
            lines.append(f"| `{e['name']}` | {e['category']} | "
                         f"{', '.join(e['where'])} | {e['note']} |")
        lines.append("")
    if result["model_file_count"]:
        shown = ", ".join(f"`{p}`" for p in result["model_files"][:8])
        more = "" if result["model_file_count"] <= 8 else f" (+{result['model_file_count'] - 8} more)"
        lines.append(f"**Model artifacts ({result['model_file_count']}):** {shown}{more}")
        lines.append("")
    if result["considerations"]:
        lines.append("**Questions to consider:**")
        for c in result["considerations"]:
            lines.append(f"- {c}")
        lines.append("")
    lines.append("_Relevance flag only — not a classification or legal advice. "
                 "Run [AI Act Companion](https://github.com/JKasteele/ai-act-companion) "
                 "for a full assessment._")
    return "\n".join(lines) + "\n"
