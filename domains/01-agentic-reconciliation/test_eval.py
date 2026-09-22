"""Focused unit tests verifying schemas, mocks, and scoring logic (zero extra dependencies)."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schemas.tools import get_bedrock_tools
from mocks.api_handlers import execute_mock_tool
from eval_runner import run_single_scenario


class TestAgenticReconciliation(unittest.TestCase):

    def test_pydantic_tool_schemas(self):
        """Verify tool schemas generate valid JSON Schema for Bedrock."""
        tools = get_bedrock_tools()
        self.assertEqual(len(tools), 4)
        tool_names = [t["toolSpec"]["name"] for t in tools]
        self.assertIn("fetch_settlement_feed", tool_names)
        self.assertIn("get_internal_ledger_entries", tool_names)
        self.assertIn("query_fx_rate", tool_names)
        self.assertIn("post_reconciliation_action", tool_names)

    def test_mock_tool_execution(self):
        """Verify deterministic mock tool responses."""
        res_fx = execute_mock_tool("query_fx_rate", {"from_currency": "USD", "to_currency": "INR"})
        self.assertEqual(res_fx["status"], "success")
        self.assertEqual(res_fx["spot_rate"], 83.92)

        res_err = execute_mock_tool("fetch_settlement_feed", {"counterparty_id": "CP-OUTAGE-503", "date": "2026-09-20"})
        self.assertEqual(res_err["status"], "error")
        self.assertEqual(res_err["http_code"], 503)

    def test_scenario_evaluation_scoring(self):
        """Verify scoring logic on nominal scenario."""
        sample_scenario = {
            "id": "SCENARIO-01",
            "category": "nominal",
            "title": "Clean Settlement Auto-Match",
            "prompt": "Reconcile settlement batch.",
            "expected_tools": ["fetch_settlement_feed", "get_internal_ledger_entries", "post_reconciliation_action"],
            "expected_action": "AUTO_MATCH"
        }
        result = run_single_scenario(None, "mock-model", sample_scenario, mock_mode=True)
        self.assertTrue(result["passed"])
        self.assertEqual(result["tools_called"], sample_scenario["expected_tools"])
        self.assertEqual(result["actions_taken"], [sample_scenario["expected_action"]])
        self.assertGreater(result["latency_ms"], 0)


if __name__ == "__main__":
    unittest.main()
