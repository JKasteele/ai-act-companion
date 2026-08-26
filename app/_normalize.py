"""Shared answer-normalisation helpers.

Every lens (classifier, security, redteam, stride, data_security, incident,
monitoring) and the report layer coerce raw intake answers the same way.
Keeping the coercion in one place means a change to how a "yes"/"no"/select
value is read is made once, not in seven copies.
"""


def truthy(value):
    """Coerce various 'yes' representations to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "ja", "on", "1"}
    return bool(value)


def as_list(value):
    """Coerce a multiselect answer to a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def select_field(answers, key):
    """Read a select/radio answer as a lowercased, stripped string (or "").

    Used by the architecture-aware severity lenses, which read only structured
    ``arch_*``/``sec_*`` select fields (never free-text) so severity stays
    injection-proof.
    """
    v = answers.get(key)
    return v.strip().lower() if isinstance(v, str) else ""
