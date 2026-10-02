# AI Evaluation & Benchmark Methodology

## Overview

The evaluation suite measures model accuracy, safety, retrieval quality, citation correctness, and response latency across real-world business queries.

---

## Evaluation Benchmark Dimensions

| Metric | Target | Description |
| :--- | :--- | :--- |
| **Intent Classification Accuracy** | $\ge 90\%$ | Correct routing into `BUSINESS_DATA`, `DOCUMENT_KNOWLEDGE`, `HYBRID`, or `GENERAL`. |
| **SQL Safety & Injection Pass Rate** | $100\%$ | Total rejection of mutating queries and adversarial SQL injection attempts. |
| **RAG Retrieval & Citation Rate** | $\ge 90\%$ | Correct identification of matching documents and inclusion of page/chunk citations. |
| **Response Latency** | $< 3500\text{ms}$ | End-to-end execution time from query receipt to synthesized response. |

---

## Benchmark Dataset (`eval/dataset.json`)

The test suite evaluates 10 standardized operational test categories:
1. **`BUSINESS_DATA`**: Monthly revenue, top product rankings, geographic territory contributions.
2. **`DOCUMENT_KNOWLEDGE`**: Enterprise refund policy, customer support SLAs.
3. **`HYBRID`**: Revenue declines cross-referenced with sales strategy documents.
4. **`ANALYTICS_ANOMALY`**: Statistical Z-score variance detection across sales and OpEx.
5. **`ANALYTICS_CUSTOMER`**: Customer repeat rate, Lifetime Value (LTV), and churn indicators.
6. **`ADVERSARIAL_INJECTION`**: Prompt injection and SQL mutation attempts (`DROP TABLE users; --`).
7. **`GENERAL`**: Conversational greetings and platform capabilities.

---

## Running the Evaluation

To execute the benchmark suite and generate the metrics report:
```bash
python eval/evaluate.py
```

The script evaluates each case, prints status updates, and exports `eval/evaluation_results.json` containing exact pass/fail scores and timing breakdowns.
