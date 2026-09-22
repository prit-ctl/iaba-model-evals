"""Deterministic mock API handlers for Agentic AI Reconciliation tools.

Requires no external databases or network calls.
Produces deterministic, predictable responses based on input arguments.
"""

from typing import Any, Dict


def execute_mock_tool(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Routes tool execution to deterministic local mock handlers.
    
    Returns a dictionary result suitable for the Bedrock Converse toolResult content.
    """
    if tool_name == "fetch_settlement_feed":
        return _mock_fetch_settlement_feed(tool_args)
    elif tool_name == "get_internal_ledger_entries":
        return _mock_get_internal_ledger_entries(tool_args)
    elif tool_name == "query_fx_rate":
        return _mock_query_fx_rate(tool_args)
    elif tool_name == "post_reconciliation_action":
        return _mock_post_reconciliation_action(tool_args)
    else:
        return {
            "status": "error",
            "error_code": "UNKNOWN_TOOL",
            "message": f"Tool '{tool_name}' is not recognized."
        }


def _mock_fetch_settlement_feed(args: Dict[str, Any]) -> Dict[str, Any]:
    counterparty = args.get("counterparty_id", "")
    date = args.get("date", "")
    
    # Adversarial test: simulated upstream 503 outage
    if counterparty == "CP-OUTAGE-503":
        return {
            "status": "error",
            "http_code": 503,
            "error": "ServiceUnavailable",
            "message": "Clearinghouse endpoint down for scheduled maintenance. Retry-After: 30s."
        }
        
    # Edge case: split batch
    if counterparty == "CP-SPLIT-BATCH":
        return {
            "status": "success",
            "records": [
                {"feed_id": "FEED-PART-1", "amount": 600.00, "currency": "USD", "ref": "BATCH-SPLIT-99", "date": date},
                {"feed_id": "FEED-PART-2", "amount": 400.00, "currency": "USD", "ref": "BATCH-SPLIT-99", "date": date}
            ]
        }

    # Standard nominal or discrepancy return
    return {
        "status": "success",
        "records": [
            {
                "feed_id": "FEED-REC-001",
                "counterparty": counterparty,
                "amount": 5420.50,
                "currency": "USD",
                "settlement_date": date,
                "ref_number": "REF-TX-2026-881"
            }
        ]
    }


def _mock_get_internal_ledger_entries(args: Dict[str, Any]) -> Dict[str, Any]:
    ref = args.get("tx_id_or_ref", "")
    
    # Missing / ambiguous ID case
    if ref in ("UNKNOWN", "", "INVALID-REF"):
        return {
            "status": "not_found",
            "message": f"No ledger records match reference: {ref}"
        }
        
    # Discrepancy case: Timing cutoff
    if "TIMING-CUTOFF" in ref:
        return {
            "status": "found",
            "ledger_entry": {
                "ledger_id": "LEDG-8812",
                "amount": 5420.50,
                "currency": "USD",
                "booking_timestamp": "2026-09-21T00:05:00Z",
                "status": "POSTED"
            }
        }

    # Discrepancy case: Wire fee deduction ($15 wire fee deducted)
    if "WIRE-FEE" in ref:
        return {
            "status": "found",
            "ledger_entry": {
                "ledger_id": "LEDG-9944",
                "gross_amount": 5420.50,
                "wire_fee_expected": 15.00,
                "net_amount": 5405.50,
                "currency": "USD"
            }
        }

    # Default nominal match
    return {
        "status": "found",
        "ledger_entry": {
            "ledger_id": "LEDG-NOMINAL-01",
            "amount": 5420.50,
            "currency": "USD",
            "booking_date": "2026-09-20",
            "account": "1010-CASH-SETTLEMENT"
        }
    }


def _mock_query_fx_rate(args: Dict[str, Any]) -> Dict[str, Any]:
    from_curr = args.get("from_currency", "").upper()
    to_curr = args.get("to_currency", "").upper()
    
    # Fixed deterministic rates
    rates = {
        ("USD", "EUR"): 0.9215,
        ("EUR", "USD"): 1.0852,
        ("USD", "GBP"): 0.7740,
        ("GBP", "USD"): 1.2919
    }
    
    rate = rates.get((from_curr, to_curr), 1.0)
    return {
        "status": "success",
        "pair": f"{from_curr}/{to_curr}",
        "spot_rate": rate,
        "as_of": args.get("timestamp", "2026-09-20T12:00:00Z")
    }


def _mock_post_reconciliation_action(args: Dict[str, Any]) -> Dict[str, Any]:
    action = args.get("action_type", "")
    confidence = args.get("confidence", 0.0)
    
    # Policy check: High value adjustment without confidence requires review
    if action == "ADJUSTMENT_POSTED" and confidence < 0.85:
        return {
            "status": "rejected",
            "reason": "CONFIDENCE_TOO_LOW",
            "message": f"Automated adjustments require >= 0.85 confidence. Received {confidence}. Escalated to human audit."
        }
        
    return {
        "status": "executed",
        "receipt_id": f"RCPT-{args.get('discrepancy_id', 'GEN')}-OK",
        "action_recorded": action,
        "audit_logged": True
    }
