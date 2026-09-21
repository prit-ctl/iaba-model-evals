# Domain 01: Agentic AI & Tool Calling

**Owner / Evaluator:** Pritesh (@pritxxh)  
**Jira Issue:** [IABA-6](https://aliuzer.atlassian.net/browse/IABA-6) / [IABA-8](https://aliuzer.atlassian.net/browse/IABA-8)  
**Topic:** Multi-System Reconciliation & Discrepancy Resolution  

---

## Directory Overview
- `schemas/`: Pydantic v2 function-calling tool interfaces.
- `datasets/`: 10 structured reconciliation test scenarios (nominal, edge-cases, error recovery).
- `mocks/`: In-memory mock handlers simulating Core Banking, Ledger, and FX APIs.
- `eval_runner.py`: Benchmark execution runner benchmarking candidate models on AWS Bedrock.
