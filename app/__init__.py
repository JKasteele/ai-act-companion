"""AI Act Companion - local AI governance toolkit.

Package layout:
  knowledge/     structured EU AI Act + NIST AI RMF knowledge base
  questionnaire  intake questionnaire definition (single source of truth)
  models         pydantic request/response models
  classifier     rule-based EU AI Act risk classifier
  reports        generators for risk assessment / DPIA / bias checklist
  storage        JSON file persistence
  main           FastAPI app
  llm/           (phase 4) optional AI agent layer
"""

__version__ = "0.7.0"
