// Presentation of engine results only. Never infer a tier from answers or labels.
export function riskClass(classification) {
  if (!classification || classification.out_of_scope) return "risk-unassessed";
  return ({
    prohibited: "risk-prohibited",
    high: "risk-high",
    limited: "risk-limited",
    minimal: "risk-minimal",
  })[classification.tier] || "risk-unassessed";
}

export function severityClass(severity) {
  return ({
    critical: "risk-prohibited", high: "risk-high",
    medium: "risk-limited", low: "risk-minimal",
  })[String(severity).toLowerCase()] || "risk-unassessed";
}
