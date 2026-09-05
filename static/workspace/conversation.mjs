export function cleanConversation(raw) {
  return (Array.isArray(raw) ? raw : []).filter(m => m && ['user', 'assistant'].includes(m.role) && typeof m.content === 'string')
    .slice(-12).map(m => ({ role: m.role, content: m.content.slice(0, 8000), sources: (Array.isArray(m.sources) ? m.sources : []).filter(s => typeof s === 'string').slice(0, 30), live: !!m.live }));
}
export function appendTurn(system, turn) {
  system.conversation = cleanConversation([...(system.conversation || []), turn]);
}
export function requestHistory(system) {
  return cleanConversation(system.conversation).slice(-8).map(({role, content}) => ({role, content: content.slice(0, 2000)}));
}
