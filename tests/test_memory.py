from nexum_core.memory.store import MemoryStore

def test_memory_roundtrip(tmp_path):
    store = MemoryStore(str(tmp_path / "memory.jsonl"))
    store.add("Nexum is an AI core", "fact")
    assert store.search("Nexum")[0]["kind"] == "fact"
