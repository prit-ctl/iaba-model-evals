"""Tool definitions for Domain 01: Agentic AI Reconciliation.

Defines Pydantic models for the 4 core reconciliation tools.
Can also convert these models directly to AWS Bedrock toolSpec JSON.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FetchSettlementFeedInput(BaseModel):
    """Input parameters for fetching external clearinghouse settlement records."""
    date: str = Field(description="ISO-8601 date string (YYYY-MM-DD) of the settlement feed.")
    counterparty_id: str = Field(default="CP-CHEX-99", description="Unique counterparty or clearinghouse identifier (e.g. CP-CHEX-99, NPCI, VISA, MASTERCARD). Defaults to 'CP-CHEX-99' if unspecified.")


class GetInternalLedgerEntriesInput(BaseModel):
    """Input parameters for querying internal accounting ledger records."""
    tx_id_or_ref: str = Field(description="Transaction ID or external settlement reference to lookup in internal ERP.")


class QueryFxRateInput(BaseModel):
    """Input parameters for fetching historical spot FX conversion rate."""
    from_currency: str = Field(description="Base currency code (e.g. USD, EUR, GBP).")
    to_currency: str = Field(description="Target currency code (e.g. USD, EUR, GBP).")
    timestamp: str = Field(description="ISO-8601 timestamp string for the valuation date.")


class PostReconciliationActionInput(BaseModel):
    """Input parameters for executing automated reconciliation action or human escalation."""
    action_type: str = Field(description="Action to take: 'AUTO_MATCH', 'ADJUSTMENT_POSTED', or 'ESCALATE_HUMAN'.")
    discrepancy_id: str = Field(description="Unique identifier for the flagged discrepancy case.")
    adjustments: Dict[str, Any] = Field(default_factory=dict, description="Adjustment metadata (e.g. fee deduction amount, delta value).")
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")


def get_bedrock_tools() -> List[Dict[str, Any]]:
    """Returns the 4 tools formatted for the AWS Bedrock Converse API toolConfig."""
    return [
        {
            "toolSpec": {
                "name": "fetch_settlement_feed",
                "description": "Retrieves clearinghouse / bank settlement statement entries for a counterparty and date.",
                "inputSchema": {
                    "json": FetchSettlementFeedInput.model_json_schema()
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_internal_ledger_entries",
                "description": "Queries internal ERP / General Ledger for matching booking records by transaction ID or reference.",
                "inputSchema": {
                    "json": GetInternalLedgerEntriesInput.model_json_schema()
                }
            }
        },
        {
            "toolSpec": {
                "name": "query_fx_rate",
                "description": "Retrieves the historical spot exchange rate between two currencies for a given date.",
                "inputSchema": {
                    "json": QueryFxRateInput.model_json_schema()
                }
            }
        },
        {
            "toolSpec": {
                "name": "post_reconciliation_action",
                "description": "Applies an automated reconciliation adjustment or flags discrepancy for human auditor review.",
                "inputSchema": {
                    "json": PostReconciliationActionInput.model_json_schema()
                }
            }
        }
    ]


def get_openai_tools() -> List[Dict[str, Any]]:
    """Returns the 4 tools formatted for OpenAI-compatible tool calling (OpenRouter/Groq)."""
    return [
        {
            "type": "function",
            "function": {
                "name": "fetch_settlement_feed",
                "description": "Retrieves clearinghouse / bank settlement statement entries for a counterparty and date.",
                "parameters": FetchSettlementFeedInput.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_internal_ledger_entries",
                "description": "Queries internal ERP / General Ledger for matching booking records by transaction ID or reference.",
                "parameters": GetInternalLedgerEntriesInput.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_fx_rate",
                "description": "Retrieves the historical spot exchange rate between two currencies for a given date.",
                "parameters": QueryFxRateInput.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "post_reconciliation_action",
                "description": "Applies an automated reconciliation adjustment or flags discrepancy for human auditor review.",
                "parameters": PostReconciliationActionInput.model_json_schema()
            }
        }
    ]
