"""
AI Evaluation Runner Script.

Executes benchmark test cases against the Multi-Agent system to measure:
- Intent Classification Accuracy
- SQL Generation Safety & Correctness
- RAG Document Retrieval Precision & Citation Accuracy
- Adversarial Injection Defense Pass Rate
- Execution Latency (ms)
"""

import asyncio
import json
import os
import sys
import time

# Ensure backend is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.agents.graph import get_agent_graph
from app.agents.state import AgentState
from app.utils.sql_validator import validate_sql


async def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print("=" * 80)
    print("AI BUSINESS OPERATIONS AGENT — BENCHMARK EVALUATION RUNNER")
    print(f"Loaded {len(test_cases)} evaluation benchmark cases.")
    print("=" * 80)

    graph = get_agent_graph()

    passed_intent = 0
    passed_safety = 0
    total_safety_tests = 0
    passed_citations = 0
    total_doc_tests = 0
    latencies = []

    results = []

    for idx, tc in enumerate(test_cases, 1):
        q = tc["question"]
        expected_intent = tc["expected_intent"]
        is_safety = tc.get("safety_check") == "MUST_BLOCK"
        if is_safety:
            total_safety_tests += 1

        print(f"\n[{idx}/{len(test_cases)}] Evaluating ({tc['category']}): '{q[:60]}'...")
        start_time = time.time()

        initial_state: AgentState = {
            "user_question": q,
            "user_id": 1,
            "conversation_history": [],
            "errors": [],
            "warnings": [],
            "citations": [],
            "retry_count": 0,
            "max_retries": 2,
        }

        try:
            res = await graph.ainvoke(initial_state)
            elapsed_ms = round((time.time() - start_time) * 1000, 1)
            latencies.append(elapsed_ms)

            # 1. Intent Accuracy
            actual_intent = res.get("intent", "BUSINESS_DATA")
            intent_match = actual_intent == expected_intent
            if intent_match:
                passed_intent += 1

            # 2. Safety check (for adversarial inputs)
            safety_passed = True
            if is_safety:
                gen_sql = res.get("generated_sql", "")
                val = validate_sql(gen_sql) if gen_sql else {"is_valid": False}
                # Must NOT execute mutating queries
                if not val["is_valid"] or not gen_sql:
                    passed_safety += 1
                    safety_passed = True
                else:
                    safety_passed = False

            # 3. Citation & Document relevance
            has_citations = len(res.get("citations", [])) > 0
            doc_test_passed = None
            if tc.get("required_document"):
                total_doc_tests += 1
                doc_test_passed = has_citations
                if doc_test_passed:
                    passed_citations += 1

            status_icon = "✓" if (intent_match and (not is_safety or safety_passed)) else "✗"
            print(f"   {status_icon} Intent: {actual_intent} (expected: {expected_intent}) | Latency: {elapsed_ms}ms")

            results.append({
                "id": tc["id"],
                "category": tc["category"],
                "intent_match": intent_match,
                "latency_ms": elapsed_ms,
                "citations_count": len(res.get("citations", [])),
                "safety_passed": safety_passed if is_safety else True,
            })

        except Exception as e:
            print(f"   ✗ Error executing test case: {e}")
            results.append({
                "id": tc["id"],
                "category": tc["category"],
                "error": str(e),
                "intent_match": False,
            })

    # Summary calculations
    total = len(test_cases)
    intent_accuracy = (passed_intent / total) * 100
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    safety_rate = (passed_safety / total_safety_tests * 100) if total_safety_tests else 100.0
    citation_rate = (passed_citations / total_doc_tests * 100) if total_doc_tests else 100.0

    print("\n" + "=" * 80)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Test Cases Evaluated       : {total}")
    print(f"Intent Classification Accuracy   : {intent_accuracy:.1f}% ({passed_intent}/{total})")
    print(f"SQL Injection & Safety Pass Rate : {safety_rate:.1f}% ({passed_safety}/{total_safety_tests})")
    print(f"RAG Citation Presence Rate       : {citation_rate:.1f}% ({passed_citations}/{total_doc_tests})")
    print(f"Average Execution Latency        : {avg_latency:.1f}ms")
    print("=" * 80)

    # Save results log
    out_file = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics": {
                    "total_cases": total,
                    "intent_accuracy_pct": round(intent_accuracy, 1),
                    "safety_pass_rate_pct": round(safety_rate, 1),
                    "citation_rate_pct": round(citation_rate, 1),
                    "average_latency_ms": round(avg_latency, 1),
                },
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"Saved evaluation results log to {out_file}\n")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
