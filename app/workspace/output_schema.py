"""Provider output grammar. Semantic, citation and size checks remain in agent.py."""


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required, "additionalProperties": False}


def response_schema(*, intake=False, plan=False, final=False):
    string = {"type": "string"}
    strings = {"type": "array", "items": string}
    properties = {"answer": string, "sources": strings}
    if intake:
        properties["proposals"] = {"type": "array", "items": obj({
            "field": string, "value": {"anyOf": [string, {"type": "boolean"}, strings]},
            "source": string, "quote": string, "reason": string,
        })}
    if plan:
        properties.update(actions={"type": "array", "items": obj({
            "title": string, "completion": string, "reason": string, "source": string, "quote": string,
        })}, questions=strings, reports=strings)
    if final:
        return obj(properties)
    # Tool turns omit answer; final turns omit tool. The orchestrator still validates
    # the chosen operation and refuses unknown tools or sources.
    properties.update(tool={"type": "string", "enum": ["read_evidence", "inspect_review"]}, source_id=string)
    return obj(properties, required=[])
