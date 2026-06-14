"""Phase 4 - optional AI agent layer.

The rule-based core (phases 1-3) works fully without this package. This layer
adds an assistant that:
  - turns a free-text description of an AI system into draft answers for the
    intake (prefill);
  - drafts narrative sections of the reports.

Design principles:
  1. HUMAN-IN-THE-LOOP IS MANDATORY. AI output is always a DRAFT that the user
     must explicitly review and confirm; never classified, submitted or stored
     automatically as final (see service.HITL_NOTICE).
  2. PLUGGABLE PROVIDER. One interface `LLMProvider` (base.py), multiple impls:
       - OllamaProvider  : local Ollama (qwen3:32b). Privacy-friendly, free.
       - ManualProvider  : generates a prompt that the user pastes into their
                           own Claude/LLM session and pastes the answer back.
                           Fits a Claude Max subscription (manual use) without
                           an API key.
  3. The classifier stays authoritative: AI only pre-fills the questionnaire;
     the deterministic rules decide the risk tier.

Module layout:
  config    settings + .env loader
  prompts   prompt builders (prefill, narrative)
  base      LLMProvider interface, JSON extraction, validation, factory
  ollama    OllamaProvider (httpx -> local Ollama)
  manual    ManualProvider (prompt for your own LLM session)
  service   high-level orchestration (used by the API)
"""

from .base import LLMProvider, get_provider  # noqa: F401
