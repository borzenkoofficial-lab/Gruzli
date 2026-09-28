from nexum_core.conversation.engine import ConversationEngine, ConversationState

def test_intent_and_context(tmp_path):
    e=ConversationEngine()
    s=ConversationState()
    x=e.observe_user(s, "Как ты работаешь?")
    assert x["intent"]=="question"
    assert x["context"]["turns"][-1]["content"]=="Как ты работаешь?"

def test_command_intent():
    e=ConversationEngine()
    assert e.classify_intent("Создай приложение")=="command"

def test_correction_intent():
    e=ConversationEngine()
    assert e.classify_intent("Нет, не так")=="correction"
