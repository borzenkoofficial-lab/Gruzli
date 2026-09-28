import json
import re
from .contracts import AgentDecision, Action

class ProtocolError(ValueError):
    pass

def _normalize(text: str) -> str:
    raw = text.strip()
    if raw.startswith('JSON:'):
        raw = raw[5:].strip()
    match = re.fullmatch(r'```(?:json)?\\s*(.*?)\\s*```', raw, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else raw

def parse_decision(text: str) -> AgentDecision:
    raw = _normalize(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return AgentDecision(kind='message', content=text)
    if not isinstance(data, dict):
        raise ProtocolError('Decision must be a JSON object')
    kind = data.get('kind', 'message')
    if kind == 'final':
        return AgentDecision(kind='final', content=str(data.get('content', '')))
    if kind != 'actions':
        return AgentDecision(kind='message', content=text)
    raw_actions = data.get('actions', [])
    if not isinstance(raw_actions, list):
        raise ProtocolError('actions must be an array')
    actions = []
    for i, item in enumerate(raw_actions):
        if not isinstance(item, dict) or not item.get('tool'):
            raise ProtocolError('every action requires a tool')
        arguments = item.get('arguments', {})
        if not isinstance(arguments, dict):
            raise ProtocolError('action arguments must be an object')
        actions.append(Action(str(item.get('id', f'action-{i+1}')), str(item['tool']), arguments, str(item.get('purpose', '')), str(item.get('success_condition', ''))))
    return AgentDecision(kind='actions', actions=actions)
