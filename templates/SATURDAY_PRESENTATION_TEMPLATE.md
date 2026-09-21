# Saturday Meeting Presentation Template (3-Slide Structure)

> **Instructions for Presenter:**  
> Keep your presentation to **5 minutes max**. Focus on concrete metrics, failure modes, and clear model trade-offs. Use the blueprint diagram attached to your Jira ticket on Slide 1.

---

## Slide 1: Domain Context & Production Architecture
- **Domain:** [Domain Title, e.g., Agentic AI: Multi-System Reconciliation]
- **Evaluator:** [Presenter Name]
- **Core Engineering Challenge:**
  - [Point 1: What makes this problem hard? e.g., Unstructured multi-source data with conflicting timestamps]
  - [Point 2: Key failure risks, e.g., Accidental incorrect balance posting or unhandled API failure]
  - [Point 3: Target production throughput and SLA requirements]
- **Visual Asset:**  
  *(Embed your attached blueprint diagram: `[Topic_Name].jpg`)*

---

## Slide 2: Benchmark Evaluation Matrix & Key Findings
- **Evaluation Dataset:** [X] real-world test cases ([Y] nominal scenarios, [Z] adversarial/edge cases).

| Model Candidate | Success / Pass Rate | Latency (p50 / p95) | Cost per 1k Txns | Top Failure Reason |
|:---|:---:|:---:|:---:|:---|
| **Primary Choice** | **95%** | 1.1s / 2.2s | $4.50 | Minor parameter verbosity |
| **Runner-Up** | **90%** | 0.8s / 1.6s | $3.80 | Hallucinated ID format on error |
| **Budget / Local** | **78%** | 0.5s / 1.0s | $0.40 | Inability to backtrack multi-step tools |

- **Key Takeaways:**
  - [Takeaway 1: Which model had the most reliable structured output?]
  - [Takeaway 2: What was the biggest surprise or unexpected failure?]

---

## Slide 3: Final Recommendation & Next Steps
- **Selected Model:** **[Model Name]**
- **Why this model wins:**
  - [Reason 1: Superior precision where errors are costly]
  - [Reason 2: Best balance of context retention and cost]
- **Fallback / Secondary Strategy:**
  - Route standard requests to [Cheaper / Faster Model], fallback to [Primary Model] upon validation failure.
- **Immediate Next Steps:**
  1. [Next step 1: Prototype production integration with guardrails]
  2. [Next step 2: Fine-tuning or few-shot prompt caching]
