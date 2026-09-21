# IABA Foundation Model Evaluation Monorepo

Welcome to the collaborative evaluation repository for project **IABA** (Model Bake-Off Initiative).

This repository is designed as a **modular, domain-isolated monorepo**. Each domain engineer has an independent workspace under `domains/` with their own dependencies, mock harnesses, test datasets, and execution scripts.

---

## Repository Structure

```text
iaba-model-evals/
├── .github/
│   ├── CODEOWNERS                     # Domain ownership approvals
│   └── workflows/
│       └── domain-isolation.yml       # PR isolation guardrails (1 domain per PR)
├── templates/                         # Shared starter templates
│   ├── EVALUATION_SCORECARD_TEMPLATE.md
│   ├── SATURDAY_PRESENTATION_TEMPLATE.md
│   └── test_cases_template.json
│
└── domains/
    ├── 01-agentic-reconciliation/     # Agentic AI & Tool Calling (Pritesh - IABA-6)
    ├── 02-rag-compliance/             # RAG Systems & Policy Knowledge (Uzer Ali - IABA-5)
    ├── 03-structured-extraction/      # Structured Clinical Extraction (Fazal Azizi - IABA-3)
    ├── 04-software-engineering/       # Monolith Modernization & Code (Arman - IABA-1)
    ├── 05-complex-reasoning/          # Supply Chain Logistics (Ayesha Riyaz - IABA-4)
    ├── 06-database-optimization/      # Database Systems & SQL Tuning (Syed Mustaqeem - IABA-7)
    └── 07-classification-triage/      # Support Ticket Triage (Abdullah Shaikh - IABA-2)
```

---

## Collaboration & Contribution Guidelines

This repository is entirely **voluntary and self-paced**:

1. **Isolation by Design:** Each folder inside `domains/` is completely decoupled. Work exclusively inside your assigned domain directory.
2. **Fork & Pull Request Workflow:**
   - Clone or Fork the repository.
   - Create a branch for your work: `git checkout -b feature/0X-my-domain`.
   - Submit a Pull Request targeting `main`.
3. **Automated Guardrail:** The CI pipeline validates that a Pull Request only touches one domain at a time to prevent accidental cross-domain modifications.

---

## AWS Bedrock Quickstart Snippet

All candidate models can be invoked via the unified AWS Bedrock `converse()` API:

```python
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

response = bedrock.converse(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    messages=[
        {"role": "user", "content": [{"text": "Hello world"}]}
    ],
    inferenceConfig={"temperature": 0.0, "maxTokens": 1024}
)

output_text = response["output"]["message"]["content"][0]["text"]
token_usage = response["usage"]
print(output_text, token_usage)
```

---

## Saturday Meeting Reference
- **Date & Time:** Saturday, September 26, 2026 · 12:00 PM – 2:00 PM IST
- **Jira Milestone:** [IABA-36](https://aliuzer.atlassian.net/browse/IABA-36)
- **Google Meet:** [https://meet.google.com/wik-upkb-zww](https://meet.google.com/wik-upkb-zww)
