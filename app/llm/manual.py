"""Manual provider: no API call.

The app composes a clean prompt that the user pastes into their OWN LLM session
(e.g. a Claude subscription); they paste the answer back into the app, where it
is parsed and validated. This uses a subscription legitimately and manually,
without an API key - and fits seamlessly with the mandatory human-in-the-loop
review step.
"""

from .base import LLMProvider


class ManualProvider(LLMProvider):
    name = "manual"
    interactive = True

    def status(self):
        return {"provider": self.name, "interactive": True, "available": True}

    def build_prompt(self, system, user):
        """Combine system+user into one paste-ready prompt for the user."""
        return (
            f"{system}\n\n"
            f"-------------------- TASK --------------------\n{user}"
        )

    def generate(self, system, user, as_json=True):
        # Interactive: not callable automatically.
        raise NotImplementedError(
            "ManualProvider does not generate by itself; use build_prompt() and "
            "let the user paste the answer back."
        )
