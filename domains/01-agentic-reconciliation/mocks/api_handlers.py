"""Deterministic mock API handlers for Agentic AI Reconciliation tools.

Configured with realistic Indian banking identifiers (UPI UTRs, NEFT, RTGS, INR balances).
Requires no external databases or network calls.
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
    
    # Adversarial test: simulated NPCI / bank gateway 503 outage
    if counterparty == "CP-OUTAGE-503":
        return {
            "status": "error",
            "http_code": 503,
            "error": "GatewayUnavailable",
            "message": "NPCI / Clearinghouse switch temporarily unavailable. Retry-After: 30s."
        }
        
    # Edge case: split QR payment batch (Tranche 1: ₹60k + Tranche 2: ₹40k = ₹1 Lakh)
    if counterparty == "CP-SPLIT-BATCH":
        return {
            "status": "success",
            "records": [
                {"feed_id": "FEED-TRANCHE-1", "amount": 60000.00, "currency": "INR", "ref": "BATCH-QR-SPLIT-88", "date": date},
                {"feed_id": "FEED-TRANCHE-2", "amount": 40000.00, "currency": "INR", "ref": "BATCH-QR-SPLIT-88", "date": date}
            ]
        }

    # Standard nominal return: UPI merchant batch
    return {
        "status": "success",
        "records": [
            {
                "feed_id": "FEED-REC-001",
                "counterparty": counterparty,
                "amount": 250000.00,
                "currency": "INR",
                "settlement_date": date,
                "ref_number": "UPI/CR/426188291042/HDFC",
                "payer_vpa": "customer@okhdfcbank"
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
        
    # Edge case: NEFT cutoff timing mismatch
    if "CUTOFF" in ref:
        return {
            "status": "found",
            "ledger_entry": {
                "ledger_id": "LEDG-NEFT-8812",
                "amount": 150000.00,
                "currency": "INR",
                "booking_timestamp": "2026-09-21T00:04:00+05:30",
                "status": "POSTED",
                "utr": "NEFT/N08226019283"
            }
        }

    # Edge case: RTGS transfer fee deduction (₹2,50,000 gross minus ₹29.50 charges = ₹2,49,970.50 net)
    if "WIRE-FEE" in ref:
        return {
            "status": "found",
            "ledger_entry": {
                "ledger_id": "LEDG-RTGS-9944",
                "gross_amount": 250000.00,
                "rtgs_charges_gst": 29.50,
                "net_amount": 249970.50,
                "currency": "INR",
                "party": "INFRA-STEEL-LTD"
            }
        }

    # Default nominal match
    return {
        "status": "found",
        "ledger_entry": {
            "ledger_id": "LEDG-NOMINAL-01",
            "amount": 250000.00,
            "currency": "INR",
            "booking_date": "2026-09-20",
            "account": "1010-HDFC-CURRENT-A/C",
            "utr": "UPI/CR/426188291042/HDFC"
        }
    }


def _mock_query_fx_rate(args: Dict[str, Any]) -> Dict[str, Any]:
    from_curr = args.get("from_currency", "").upper()
    to_curr = args.get("to_currency", "").upper()
    
    # Deterministic RBI reference conversion rates
    rates = {
        ("USD", "INR"): 83.92,
        ("INR", "USD"): 0.0119,
        ("EUR", "INR"): 93.45,
        ("INR", "EUR"): 0.0107,
        ("GBP", "INR"): 111.20,
        ("INR", "GBP"): 0.0090
    }
    
    rate = rates.get((from_curr, to_curr), 1.0)
    return {
        "status": "success",
        "pair": f"{from_curr}/{to_curr}",
        "spot_rate": rate,
        "as_of": args.get("timestamp", "2026-09-20T12:00:00+05:30"),
        "source": "RBI_REFERENCE_RATE"
    }


def _mock_post_reconciliation_action(args: Dict[str, Any]) -> Dict[str, Any]:
    action = args.get("action_type", "")
    confidence = args.get("confidence", 0.0)
    
    # Safeguard check: High value adjustment without high confidence requires human escalation
    if action == "ADJUSTMENT_POSTED" and confidence < 0.85:
        return {
            "status": "rejected",
            "reason": "CONFIDENCE_TOO_LOW",
            "message": f"Automated adjustments require >= 0.85 confidence. Received {confidence}. Escalated to auditor."
        }
        
    return {
        "status": "executed",
        "receipt_id": f"RCPT-REC-{args.get('discrepancy_id', 'IN')}-OK",
        "action_recorded": action,
        "audit_logged": True
    }
