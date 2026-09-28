import unittest
from nexum_core.reasoning.planner import Planner

class PlannerVerificationTests(unittest.TestCase):
    def test_build_task_gets_build_and_test_steps(self):
        plan = Planner().build("build and test the project", [], ["list_files", "read_file", "search_files", "run_command"])
        ids = [step.id for step in plan.steps]
        self.assertEqual(ids, ["inspect", "build", "test"])
        self.assertIn("run_command", plan.steps[1].tools)

if __name__ == "__main__":
    unittest.main()
