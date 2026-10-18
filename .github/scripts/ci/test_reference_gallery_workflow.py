from itertools import product
from pathlib import Path
import re
import unittest


GITHUB = Path(__file__).resolve().parents[2]


class ReferenceGalleryWorkflowTest(unittest.TestCase):
    def setUp(self):
        workflow = (GITHUB / "workflows/build.yml").read_text()
        job = workflow.split("  macos-predicate-tests:\n", 1)[1].split("\n  android-eligibility:\n", 1)[0]
        self.steps = dict(block.split("\n", 1) for block in job.split("      - name: ")[1:])

    def outcome(self, name, value):
        step_id = re.search(r"^        id: (\w+)$", self.steps[name], re.M)[1]
        return {step_id: value}

    def selected(self, name, outcomes, event, cancelled, previous_success):
        condition = re.search(r"^        if: \$\{\{ (.+) \}\}$", self.steps[name], re.M)[1]
        # Actions implicitly requires success() unless a status function is present.
        if not re.search(r"\b(success|failure|cancelled|always)\(", condition) and not previous_success:
            return False
        condition = re.sub(r"steps\.(\w+)\.outcome", lambda match: repr(outcomes.get(match[1], "skipped")), condition)
        condition = condition.replace("github.event_name", "event").replace("&&", "and")
        condition = re.sub(r"!(?!=)", "not ", condition)
        return eval(condition, {"__builtins__": {}}, {
            "event": event, "cancelled": lambda: cancelled,
            "success": lambda: previous_success, "failure": lambda: not previous_success,
            "always": lambda: True,
        })

    def test_generation_requires_reporting_setup_but_survives_unrelated_failures(self):
        for outcome, event, cancelled, previous_success in product(
            ("success", "failure", "skipped"), ("pull_request", "push"), (False, True), (False, True),
        ):
            with self.subTest(outcome=outcome, event=event, cancelled=cancelled, previous_success=previous_success):
                outcomes = self.outcome("Prepare the visual reporting environment", outcome)
                self.assertEqual(
                    self.selected("Generate the PR reference gallery", outcomes, event, cancelled, previous_success),
                    outcome == "success" and event == "pull_request" and not cancelled,
                )

    def test_retention_requires_successful_generation(self):
        for outcome, event, cancelled, previous_success in product(
            ("success", "failure", "skipped"), ("pull_request", "push"), (False, True), (False, True),
        ):
            with self.subTest(outcome=outcome, event=event, cancelled=cancelled, previous_success=previous_success):
                outcomes = self.outcome("Generate the PR reference gallery", outcome)
                self.assertEqual(
                    self.selected("Retain the reference gallery", outcomes, event, cancelled, previous_success),
                    outcome == "success" and event == "pull_request" and not cancelled,
                )


if __name__ == "__main__":
    unittest.main()
