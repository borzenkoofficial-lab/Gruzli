import json
from .contracts import AgentDecision, Action

class ProtocolError(ValueError):
    pass

def parse_decision(text: str) -> AgentDecision:
    raw=text.strip()
    if raw.startswith('JSON:'): raw=raw[5:].strip()
    try: data=json.loads(raw)
    except json.JSONDecodeError: return AgentDecision(kind='message', content=text)
    kind=data.get('kind','message')
    if kind=='final': return AgentDecision(kind='final', content=str(data.get('content','')))
    if kind!='actions': return AgentDecision(kind='message', content=text)
    actions=[]
    for i,item in enumerate(data.get('actions',[])):
        if not item.get('tool'): raise ProtocolError('action tool is required')
        actions.append(Action(str(item.get('id',f'action-{i+1}')), item['tool'], item.get('arguments',{}), str(item.get('purpose','')), str(item.get('success_condition',''))))
    return AgentDecision(kind='actions', actions=actions)