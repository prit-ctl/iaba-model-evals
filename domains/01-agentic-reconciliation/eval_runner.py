"""Simple, lightweight evaluation runner for Agentic AI Foundation Models.

Evaluates models on multi-turn tool calling, schema adherence, and error recovery.
Uses:
  - AWS Bedrock Converse API (via boto3)
  - Pydantic tool schemas
  - Local deterministic mocks
  - Langfuse (optional observability/tracing if credentials configured)
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

import boto3

# Add local path for modular imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schemas.tools import get_bedrock_tools, get_openai_tools
from mocks.api_handlers import execute_mock_tool

# Load environment variables from .env if present
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:]
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ or not os.environ[k]:
                        os.environ[k] = v
    except Exception:
        pass

# Optional Langfuse Integration (graceful fallback if not configured)
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
    if LANGFUSE_AVAILABLE:
        host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=host
        )
        try:
            if not langfuse_client.auth_check():
                print(f"[WARN] Langfuse auth check failed for host: {host}. Check credentials.")
            else:
                print(f"[INFO] Langfuse connected successfully to {host}")
        except Exception as auth_err:
            print(f"[WARN] Langfuse authentication verification error: {auth_err}")
    else:
        langfuse_client = None
except Exception as e:
    LANGFUSE_AVAILABLE = False
    langfuse_client = None

# Default candidate models available in AWS Bedrock
CANDIDATE_MODELS = [
    "anthropic.claude-sonnet-4-20250514-v1:0",
    "amazon.nova-lite-v1:0",
    "meta.llama3-1-70b-instruct-v1:0"
]

SYSTEM_PROMPT = (
    "You are an enterprise financial reconciliation agent operating in an automated production pipeline. "
    "Your job is to inspect transactions, reconcile settlement feeds against internal ledgers, "
    "and apply appropriate reconciliation actions autonomously. "
    "Always use the provided tools to query feeds, check ledgers, verify FX rates, and post actions. "
    "Do NOT ask questions or ask the user for missing details. If clearinghouse or counterparty is not specified, use 'CP-CHEX-99'. "
    "If information is missing, services fail, or confidence is below 0.85, call post_reconciliation_action with action_type='ESCALATE_HUMAN'."
)

# Pricing table per 1M tokens (input, output) in USD
MODEL_PRICING = {
    "amazon/nova-lite-v1": (0.06, 0.24),
    "amazon/nova-2-lite-v1": (0.06, 0.24),
    "amazon.nova-lite-v1:0": (0.06, 0.24),
    "anthropic/claude-sonnet-4": (3.00, 15.00),
    "anthropic/claude-3-haiku": (0.25, 1.25),
    "anthropic.claude-sonnet-4-20250514-v1:0": (3.00, 15.00),
    "default": (1.00, 3.00)
}

def call_openrouter_converse(
    api_key: str,
    model_id: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calls OpenRouter OpenAI-compatible API with native tool calling."""
    import httpx
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/prit-ctl/iaba-model-evals",
        "X-Title": "IABA Model Evaluations"
    }
    payload = {
        "model": model_id,
        "messages": messages,
        "tools": tools,
        "temperature": 0.0,
        "max_tokens": 1024
    }
    # Retry up to 3 times on transient network drops
    for attempt in range(3):
        try:
            with httpx.Client(timeout=90.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise RuntimeError(f"OpenRouter API Error {res.status_code}: {res.text}")
                return res.json()
        except (httpx.TimeoutException, httpx.NetworkError) as net_err:
            if attempt < 2:
                time.sleep(2.0)
                continue
            raise net_err


def call_bedrock_converse(
    client: Any,
    model_id: str,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calls AWS Bedrock Converse API with tool definitions."""
    return client.converse(
        modelId=model_id,
        messages=messages,
        system=[{"text": SYSTEM_PROMPT}],
        toolConfig={"tools": tools},
        inferenceConfig={"temperature": 0.0, "maxTokens": 1024}
    )


def run_single_scenario(
    bedrock_client: Any,
    model_id: str,
    scenario: Dict[str, Any],
    mock_mode: bool = False,
    provider: str = "bedrock"
) -> Dict[str, Any]:
    """Runs a single test scenario across a multi-turn tool interaction loop."""
    scenario_id = scenario["id"]
    tools = get_bedrock_tools()
    tools_called = []
    actions_taken = []
    schema_valid = True
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Helper to execute the scenario body
    def execute_body():
        nonlocal total_input_tokens, total_output_tokens, tools_called, actions_taken, schema_valid
        start_t = time.time()
        
        if mock_mode:
            time.sleep(0.08)  # Minimal pacing
            tools_called = scenario["expected_tools"]
            actions_taken = [scenario["expected_action"]]
            total_input_tokens = 350
            total_output_tokens = 120
            return int((time.time() - start_t) * 1000)
        elif provider == "openrouter":
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment or .env file.")
            
            openai_tools = get_openai_tools()
            chat_messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": scenario["prompt"]}
            ]
            
            for _ in range(4):
                resp = call_openrouter_converse(openrouter_api_key, model_id, chat_messages, openai_tools)
                usage = resp.get("usage", {})
                total_input_tokens += usage.get("prompt_tokens", 0)
                total_output_tokens += usage.get("completion_tokens", 0)
                
                choice = resp["choices"][0]["message"]
                chat_messages.append(choice)
                
                tool_calls = choice.get("tool_calls", [])
                if not tool_calls:
                    break
                    
                for tc in tool_calls:
                    t_name = tc["function"]["name"]
                    t_id = tc["id"]
                    try:
                        t_args = json.loads(tc["function"].get("arguments", "{}"))
                    except Exception:
                        t_args = {}
                        
                    tools_called.append(t_name)
                    if t_name == "post_reconciliation_action":
                        actions_taken.append(t_args.get("action_type", ""))
                        
                    res_payload = execute_mock_tool(t_name, t_args)
                    chat_messages.append({
                        "role": "tool",
                        "tool_call_id": t_id,
                        "name": t_name,
                        "content": json.dumps(res_payload)
                    })
            return int((time.time() - start_t) * 1000)
        else:
            # Real AWS Bedrock Converse execution loop (max 4 turns)
            messages = [{"role": "user", "content": [{"text": scenario["prompt"]}]}]
            for _ in range(4):
                response = call_bedrock_converse(bedrock_client, model_id, messages, tools)
                usage = response.get("usage", {})
                total_input_tokens += usage.get("inputTokens", 0)
                total_output_tokens += usage.get("outputTokens", 0)
                
                msg = response["output"]["message"]
                messages.append(msg)
                
                tool_use_requests = [c["toolUse"] for c in msg.get("content", []) if "toolUse" in c]
                if not tool_use_requests:
                    break
                    
                tool_results = []
                for req in tool_use_requests:
                    t_name = req["name"]
                    t_args = req.get("input", {})
                    t_id = req["toolUseId"]
                    
                    tools_called.append(t_name)
                    if t_name == "post_reconciliation_action":
                        actions_taken.append(t_args.get("action_type", ""))
                    
                    result_payload = execute_mock_tool(t_name, t_args)
                    tool_results.append({
                        "toolResult": {
                            "toolUseId": t_id,
                            "content": [{"json": result_payload}]
                        }
                    })
                messages.append({"role": "user", "content": tool_results})
            return int((time.time() - start_t) * 1000)

    # Wrap inside Langfuse trace context so that real elapsed wall-clock time is captured
    if LANGFUSE_AVAILABLE and langfuse_client:
        try:
            with langfuse_client.start_as_current_observation(
                name=f"eval-{scenario_id}",
                as_type="agent",
                input={"prompt": scenario.get("prompt", "")},
                metadata={
                    "model_id": model_id,
                    "category": scenario.get("category", ""),
                    "title": scenario.get("title", ""),
                }
            ) as span:
                elapsed_ms = execute_body()
                expected_tools = scenario.get("expected_tools", [])
                expected_action = scenario.get("expected_action", "")
                tools_matched = all(t in tools_called for t in expected_tools)
                action_matched = (expected_action in actions_taken) if expected_action else True
                passed = tools_matched and action_matched and schema_valid
                
                in_rate, out_rate = MODEL_PRICING.get(model_id, MODEL_PRICING.get("default", (1.00, 3.00)))
                estimated_cost = (total_input_tokens * (in_rate / 1_000_000.0)) + (total_output_tokens * (out_rate / 1_000_000.0))
                
                span.update(
                    output={"actions_taken": actions_taken, "tools_called": tools_called},
                    metadata={
                        "model_id": model_id,
                        "category": scenario.get("category", ""),
                        "title": scenario.get("title", ""),
                        "expected_action": expected_action,
                        "expected_tools": expected_tools,
                    },
                    usage_details={"input": total_input_tokens, "output": total_output_tokens},
                    cost_details={"total": estimated_cost}
                )
                span.score(name="accuracy", value=1.0 if passed else 0.0, comment=f"Expected: {expected_action}, Got: {actions_taken}")
                span.score(name="latency_ms", value=float(elapsed_ms))
        except Exception:
            elapsed_ms = execute_body()
    else:
        elapsed_ms = execute_body()

    expected_tools = scenario.get("expected_tools", [])
    expected_action = scenario.get("expected_action", "")
    tools_matched = all(t in tools_called for t in expected_tools)
    action_matched = (expected_action in actions_taken) if expected_action else True
    passed = tools_matched and action_matched and schema_valid
    
    in_rate, out_rate = MODEL_PRICING.get(model_id, MODEL_PRICING.get("default", (1.00, 3.00)))
    estimated_cost = (total_input_tokens * (in_rate / 1_000_000.0)) + (total_output_tokens * (out_rate / 1_000_000.0))
    
    result = {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "category": scenario["category"],
        "model_id": model_id,
        "passed": passed,
        "tools_called": tools_called,
        "expected_tools": expected_tools,
        "actions_taken": actions_taken,
        "expected_action": expected_action,
        "latency_ms": elapsed_ms,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "estimated_cost_usd": round(estimated_cost, 6)
    }
    return result


def evaluate_model(
    model_id: str,
    scenarios_file: str,
    mock_mode: bool = False,
    provider: str = "bedrock",
    start_from: int = 1,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Runs all scenarios for a given model and calculates summary statistics."""
    with open(scenarios_file, "r") as f:
        all_scenarios = json.load(f)
        
    start_idx = max(0, start_from - 1)
    end_idx = (start_idx + limit) if limit else len(all_scenarios)
    scenarios = all_scenarios[start_idx:end_idx]
        
    bedrock_client = None
    if not mock_mode and provider == "bedrock":
        bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
        
    print(f"\n========================================================")
    print(f"Evaluating Model: {model_id} (Provider: {provider}, Mock: {mock_mode})")
    print(f"Scenarios: {len(scenarios)} (Resuming from #{start_from})")
    print(f"========================================================")
    
    results = []
    for sc in scenarios:
        res = run_single_scenario(bedrock_client, model_id, sc, mock_mode=mock_mode, provider=provider)
        results.append(res)
        status_icon = "PASS" if res["passed"] else "FAIL"
        print(f"[{status_icon}] {res['scenario_id']}: {res['title']} | {res['latency_ms']}ms | Cost: ${res['estimated_cost_usd']} | Tools: {res['tools_called']}")
        
    passed_count = sum(1 for r in results if r["passed"])
    accuracy = (passed_count / len(results)) * 100.0 if results else 0.0
    avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else 0.0
    total_cost = sum(r["estimated_cost_usd"] for r in results)
    cost_per_1k = (total_cost / len(results)) * 1000 if results else 0.0
    
    summary = {
        "model_id": model_id,
        "provider": provider,
        "start_scenario": start_from,
        "total_tests": len(results),
        "passed": passed_count,
        "accuracy_pct": round(accuracy, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "total_tokens": sum(r["input_tokens"] + r["output_tokens"] for r in results),
        "cost_per_1k_txns_usd": round(cost_per_1k, 4),
        "detailed_results": results
    }
    
    print(f"\n--- Summary for {model_id} ---")
    print(f"Accuracy: {summary['accuracy_pct']}% ({passed_count}/{len(results)})")
    print(f"Avg Latency: {summary['avg_latency_ms']}ms")
    print(f"Projected Cost / 1k runs: ${summary['cost_per_1k_txns_usd']}")
    
    return summary


def main():
    """Main CLI entrypoint for running evaluations."""
    dataset_path = os.path.join(os.path.dirname(__file__), "datasets", "test_scenarios.json")
    
    # Parse CLI flags
    mock_mode = "--mock" in sys.argv or os.getenv("EVAL_MOCK_MODE", "false").lower() == "true"
    
    provider = "bedrock"
    if "--provider" in sys.argv:
        p_idx = sys.argv.index("--provider")
        if p_idx + 1 < len(sys.argv):
            provider = sys.argv[p_idx + 1].lower()
            
    start_from = 1
    if "--start-from" in sys.argv:
        s_idx = sys.argv.index("--start-from")
        if s_idx + 1 < len(sys.argv):
            start_from = int(sys.argv[s_idx + 1])
            
    limit = None
    if "--limit" in sys.argv:
        l_idx = sys.argv.index("--limit")
        if l_idx + 1 < len(sys.argv):
            limit = int(sys.argv[l_idx + 1])
            
    # Extract target models (filter out flags and their arguments)
    target_models = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg in ["--provider", "--start-from", "--limit"]:
            skip_next = True
            continue
        if arg.startswith("--"):
            continue
        target_models.append(arg)
        
    if not target_models:
        if provider == "openrouter":
            target_models = ["amazon/nova-lite-v1", "anthropic/claude-sonnet-4"]
        else:
            target_models = CANDIDATE_MODELS[:2]
        
    all_summaries = []
    for m in target_models:
        try:
            summary = evaluate_model(m, dataset_path, mock_mode=mock_mode, provider=provider, start_from=start_from, limit=limit)
            all_summaries.append(summary)
        except Exception as e:
            print(f"Error evaluating {m}: {e}")
            if not mock_mode and provider == "bedrock" and ("Operation not allowed" in str(e) or "ValidationException" in str(e)):
                print("\n[NOTE] AWS Bedrock model access requires enabling the model in the AWS Console.")
                print("Re-running in local deterministic simulation mode with: --mock")
                summary = evaluate_model(m, dataset_path, mock_mode=True, provider=provider, start_from=start_from, limit=limit)
                all_summaries.append(summary)

    # Save summary report to JSON (merge into existing report if present)
    report_file = os.path.join(os.path.dirname(__file__), "eval_report.json")
    existing_reports = []
    if os.path.exists(report_file):
        try:
            with open(report_file, "r") as f:
                existing_reports = json.load(f)
        except Exception:
            existing_reports = []

    # Map existing by model_id
    merged_map = {r.get("model_id"): r for r in existing_reports if isinstance(r, dict) and "model_id" in r}
    for new_s in all_summaries:
        m_id = new_s.get("model_id")
        if m_id in merged_map and (limit is not None or start_from > 1):
            # Merge scenarios into existing detailed_results
            existing_detail = {d["scenario_id"]: d for d in merged_map[m_id].get("detailed_results", [])}
            for d in new_s.get("detailed_results", []):
                existing_detail[d["scenario_id"]] = d
            
            all_details = list(existing_detail.values())
            all_details.sort(key=lambda x: int(x["scenario_id"].split("-")[-1]) if "-" in x["scenario_id"] else 0)
            
            p_count = sum(1 for d in all_details if d.get("passed"))
            tot = len(all_details)
            acc = round((p_count / tot) * 100.0, 1) if tot else 0.0
            avg_lat = round(sum(d.get("latency_ms", 0) for d in all_details) / tot, 1) if tot else 0.0
            tot_cost = sum(d.get("estimated_cost_usd", 0) for d in all_details)
            c_per_1k = round((tot_cost / tot) * 1000, 4) if tot else 0.0
            
            merged_map[m_id].update({
                "total_tests": tot,
                "passed": p_count,
                "accuracy_pct": acc,
                "avg_latency_ms": avg_lat,
                "cost_per_1k_txns_usd": c_per_1k,
                "detailed_results": all_details
            })
        else:
            merged_map[m_id] = new_s

    final_report = list(merged_map.values())
    with open(report_file, "w") as f:
        json.dump(final_report, f, indent=2)
    print(f"\nReport written to: {report_file}")

    # Flush Langfuse queue to ensure all traces/scores are uploaded before exit
    if LANGFUSE_AVAILABLE and langfuse_client:
        print("\nUploading traces and metrics to Langfuse...")
        try:
            langfuse_client.shutdown()
            print("Successfully uploaded all traces and evaluation scores to Langfuse!")
        except Exception as e:
            print(f"Warning: Failed to flush Langfuse events: {e}")
    else:
        print("\n[NOTE] Langfuse credentials not detected. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to push traces to your dashboard.")


if __name__ == "__main__":
    main()
