import json
import tempfile
import unittest
from pathlib import Path

from mlops_readiness.cases import EvalCase, load_cases
from mlops_readiness.metrics import deployment_readiness, evaluate_cases, summarize_results
from mlops_readiness.providers import RuleBasedModel


class EvalHarnessTests(unittest.TestCase):
    def test_load_cases_from_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.jsonl"
            path.write_text(
                '{"id":"case-1","input":"reset password","expected":{"contains":["password"]},"tags":["support"]}\n',
                encoding="utf-8",
            )

            cases = load_cases(path)

        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].id, "case-1")
        self.assertEqual(cases[0].expected["contains"], ["password"])

    def test_evaluate_cases_scores_exact_and_contains_expectations(self):
        cases = load_cases(Path(__file__).parents[1] / "data" / "sample_cases.jsonl")
        model = RuleBasedModel()

        results = evaluate_cases(cases, model)
        summary = summarize_results(results)

        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["passed"], 5)
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["failed_ids"], [])

    def test_deployment_readiness_blocks_low_pass_rate(self):
        readiness = deployment_readiness(
            {"total": 10, "passed": 7, "pass_rate": 0.7, "failed_ids": ["x", "y", "z"]},
            min_pass_rate=0.9,
        )

        self.assertFalse(readiness["ready"])
        self.assertIn("pass_rate 0.700 below threshold 0.900", readiness["checks"])

    def test_cli_json_report_shape(self):
        from mlops_readiness.runner import run_evaluation

        report = run_evaluation(
            cases_path=Path(__file__).parents[1] / "data" / "sample_cases.jsonl",
            model_name="rule-based",
            min_pass_rate=1.0,
        )

        json.dumps(report)
        self.assertTrue(report["readiness"]["ready"])
        self.assertEqual(report["summary"]["pass_rate"], 1.0)
        self.assertEqual(report["model"], "rule-based")

    def test_load_run_config_from_json_file(self):
        from mlops_readiness.runner import load_run_config

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "readiness.json"
            config_path.write_text(
                json.dumps(
                    {
                        "cases": "data/sample_cases.jsonl",
                        "model": "rule-based",
                        "min_pass_rate": 0.95,
                        "output": "reports/readiness-report.json",
                    }
                ),
                encoding="utf-8",
            )

            config = load_run_config(config_path)

        self.assertEqual(config["cases"], Path("data/sample_cases.jsonl"))
        self.assertEqual(config["model"], "rule-based")
        self.assertEqual(config["min_pass_rate"], 0.95)
        self.assertEqual(config["output"], Path("reports/readiness-report.json"))

    def test_validate_min_pass_rate_rejects_out_of_range_values(self):
        from mlops_readiness.runner import validate_min_pass_rate

        with self.assertRaises(ValueError):
            validate_min_pass_rate(-0.01)
        with self.assertRaises(ValueError):
            validate_min_pass_rate(1.01)
        self.assertEqual(validate_min_pass_rate(0.95), 0.95)

    def test_load_cases_rejects_unknown_expectation_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.jsonl"
            path.write_text(
                '{"id":"case-1","input":"hello","expected":{"regex":"hello"},"tags":[]}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unsupported expectation key"):
                load_cases(path)

    def test_load_cases_rejects_invalid_expectation_shapes(self):
        invalid_cases = [
            '{"id":"case-1","input":"hello","expected":{"contains":"hello"},"tags":[]}\n',
            '{"id":"case-2","input":"hello","expected":{"exact":true},"tags":[]}\n',
            '{"id":"case-3","input":"hello","expected":{"json_contains":["status"]},"tags":[]}\n',
        ]
        for raw_case in invalid_cases:
            with self.subTest(raw_case=raw_case):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "cases.jsonl"
                    path.write_text(raw_case, encoding="utf-8")

                    with self.assertRaises(ValueError):
                        load_cases(path)

    def test_json_contains_expectation_matches_structured_output(self):
        class JsonModel:
            name = "json-model"

            def predict(self, text):
                return '{"status":"ok","ready":true,"ignored":"metadata"}'

        case = EvalCase(
            id="json-contract",
            input="Return readiness JSON",
            expected={"json_contains": {"status": "ok", "ready": True}},
            tags=["contract"],
        )

        result = evaluate_cases([case], JsonModel())[0]

        self.assertTrue(result.passed)

    def test_json_contains_expectation_reports_structured_mismatch(self):
        class JsonModel:
            name = "json-model"

            def predict(self, text):
                return '{"status":"ok","ready":false}'

        case = EvalCase(
            id="json-contract",
            input="Return readiness JSON",
            expected={"json_contains": {"ready": True}},
            tags=["contract"],
        )

        result = evaluate_cases([case], JsonModel())[0]

        self.assertFalse(result.passed)
        self.assertEqual(result.reason, "JSON value mismatch at $.ready: expected True, got False")

    def test_summary_includes_tag_pass_rates(self):
        cases = load_cases(Path(__file__).parents[1] / "data" / "sample_cases.jsonl")
        results = evaluate_cases(cases, RuleBasedModel())

        summary = summarize_results(results)

        self.assertEqual(summary["by_tag"]["support"]["total"], 2)
        self.assertEqual(summary["by_tag"]["support"]["passed"], 2)
        self.assertEqual(summary["by_tag"]["support"]["pass_rate"], 1.0)

    def test_report_includes_reproducibility_metadata(self):
        from mlops_readiness.runner import run_evaluation

        report = run_evaluation(
            cases_path=Path(__file__).parents[1] / "data" / "sample_cases.jsonl",
            model_name="rule-based",
            min_pass_rate=1.0,
        )

        self.assertIn("generated_at_utc", report["metadata"])
        self.assertEqual(report["metadata"]["tool"], "mlops-readiness-scaffold")
        self.assertEqual(report["metadata"]["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main()
