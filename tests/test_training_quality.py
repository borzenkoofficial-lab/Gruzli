import unittest
from nexum_core.training.quality import DatasetQuality

class QualityTests(unittest.TestCase):
    def test_verified_trace_is_accepted(self):
        record = {
            "task": "build app",
            "messages": [{"role": "assistant", "content": "done"}],
            "actions": [{"name": "build"}],
            "observations": [{"exit_code": 0}],
            "verification": {"ok": True},
            "success": True,
        }
        decision = DatasetQuality().evaluate(record)
        self.assertTrue(decision.accepted)
        self.assertGreaterEqual(decision.score, 0.7)

    def test_unverified_trace_is_rejected(self):
        record = {
            "task": "build app",
            "messages": [{"role": "assistant", "content": "done"}],
            "actions": [{"name": "build"}],
            "observations": [],
            "verification": {"ok": False},
            "success": False,
        }
        self.assertFalse(DatasetQuality().evaluate(record).accepted)

    def test_duplicates_are_removed(self):
        q = DatasetQuality()
        record = {
            "task": "same",
            "messages": [{"role": "assistant", "content": "answer"}],
            "actions": [{"name": "run"}],
            "observations": [{"ok": True}],
            "verification": {"ok": True},
            "success": True,
        }
        self.assertEqual(len(q.filter([record, dict(record)])), 1)

if __name__ == "__main__":
    unittest.main()
