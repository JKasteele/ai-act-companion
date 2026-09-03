"""Hosted Anthropic (Claude Sonnet 5) provider, guarded by a spend cap.

Calls the real Claude API for a public demo, but only within a small budget
(see budget.py: a lifetime USD cap, a daily call cap, a per-IP daily cap).
When any cap is hit, service.provider_for() degrades to the `replay` provider
instead of calling this class - so this module never needs to enforce the cap
itself, only report the SDK call's usage back to budget.record().

The API key is read by the Anthropic SDK directly from ANTHROPIC_API_KEY - it
is never stored on this object, never logged, never echoed in status().
"""

import os

from . import budget
from .base import LLMProvider
from .config import settings

# The stable "FIELDS (id [type]: question): ..." digest in the prefill user
# prompt (see prompts.py) is identical on every call; splitting it into its
# own cached system block avoids re-paying for it each time. Narrative prompts
# don't contain this marker, so they fall back to a single system block.
_FIELDS_MARKER = "DESCRIPTION OF THE AI SYSTEM:"


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    interactive = False

    def __init__(self):
        self.model = settings.anthropic_model

    def status(self):
        """No network call here - status is a local availability check only."""
        info = {"provider": self.name, "interactive": False, "available": False,
                 "model": self.model, "budget": budget.state()}
        try:
            import anthropic  # noqa: F401
        except ImportError as e:
            info["error"] = f"anthropic SDK not installed: {e}"
            return info
        if not os.environ.get("ANTHROPIC_API_KEY"):
            info["error"] = "ANTHROPIC_API_KEY is not set."
            return info
        info["available"] = True
        return info

    def generate(self, system, user, as_json=True):
        import anthropic

        # Lazy client construction: importing this module (or building the
        # provider for a status() check) must never require a key.
        client = anthropic.Anthropic()

        if _FIELDS_MARKER in user:
            idx = user.index(_FIELDS_MARKER)
            fields_part, user_part = user[:idx], user[idx:]
            system_blocks = [
                {"type": "text", "text": system},
                {"type": "text", "text": fields_part,
                 "cache_control": {"type": "ephemeral"}},
            ]
        else:
            system_blocks = [{"type": "text", "text": system}]
            user_part = user

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                output_config={"effort": "low"},
                system=system_blocks,
                messages=[{"role": "user", "content": user_part}],
            )
        except anthropic.AuthenticationError as e:
            raise RuntimeError("Anthropic API key rejected") from e

        budget.record(response.usage, self.model)

        if response.stop_reason == "refusal":
            return ""
        return "".join(block.text for block in response.content if block.type == "text")
