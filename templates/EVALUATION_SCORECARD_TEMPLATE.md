# Model Evaluation Scorecard Template

**Domain Evaluation:** [Insert Domain Name, e.g., Agentic AI / RAG Systems / Structured Extraction]  
**Evaluator / Assignee:** [Your Name]  
**Target Submission Date:** Saturday Presentation

---

## 1. Executive Summary

| Recommendation Tier | Model Candidate | Primary Justification | Key Caveat / Constraint |
|:---|:---|:---|:---|
| 🥇 **Primary Choice** | [e.g., Claude 3.5 Sonnet] | Highest accuracy (94%) & reliable tool calling | Higher per-token cost on bulk input |
| 🥈 **Secondary / Fallback** | [e.g., GPT-4o] | Sub-second latency, broad enterprise tooling | Occasional schema hallucination on edge cases |
| 🥉 **Cost-Optimized / Local** | [e.g., Qwen 2.5 Coder 32B] | Zero external data egress, lowest operational cost | Lower complex reasoning ceiling |

---

## 2. Benchmark Comparison Matrix

*Fill in the observed metrics based on your 5–10 representative test cases.*

| Model Name | Eval / Success Rate (%) | Latency p50 (ms) | Latency p95 (ms) | Avg Tokens (In / Out) | Projected Cost / 1k Txns ($) | Failure Modes Encountered | Production Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|:---|:---:|
| **Claude 3.5 Sonnet** | % | ms | ms | / | $ | | Recommended |
| **GPT-4o** | % | ms | ms | / | $ | | Alternative |
| **Gemini 1.5 Pro** | % | ms | ms | / | $ | | Backup |
| **Open Weights / Local** | % | ms | ms | / | $ | | Feasibility Check |

---

## 3. Qualitative Assessment

### A. Strengths Observed
- **[Model Name]:** [Detail specific strengths, e.g., strict JSON compliance, handling multi-turn tool recovery, precise grounding without hallucinations.]

### B. Failure Modes & Edge-Case Vulnerabilities
- **[Model Name]:** [Detail failure cases, e.g., syntax errors, parameter drops, unhandled exceptions on malformed input.]

### C. Enterprise Readiness & Implementation Risk
- **Security & Privacy:** [Data retention policies, private VPC endpoints, PII redaction requirements]
- **Rate Limits & Scalability:** [Token per minute (TPM) limits, concurrent request handling]
- **Fallback Strategy:** [Automated retry with smaller model, human-in-the-loop escalation threshold]
