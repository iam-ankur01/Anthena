"""Agent evaluation script — measures routing accuracy.

Runs each test case through the agent and checks whether the correct
tool was invoked. Prints a summary table with per-case pass/fail
and overall accuracy.

Usage:
    python -m evaluation.eval_agent

Requires:
    - OPENAI_API_KEY set in environment or .env
    - At least one document uploaded (for document tool test cases)
"""

import json
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agent.graph import compiled_graph


def load_test_cases() -> list[dict]:
    """Load test cases from the JSON file."""
    test_cases_path = Path(__file__).parent / "test_cases.json"
    with open(test_cases_path) as f:
        return json.load(f)


def evaluate_single_case(test_case: dict) -> dict:
    """Run a single test case through the agent and check routing.

    Returns a result dict with:
        - id, question, expected_tool, actual_tools, passed, answer_preview
    """
    question = test_case["question"]
    expected_tool = test_case["expected_tool"]

    try:
        result = compiled_graph.invoke({
            "messages": [HumanMessage(content=question)],
            "tools_used": [],
        })

        actual_tools = result.get("tools_used", [])
        final_answer = result["messages"][-1].content

        passed = expected_tool in actual_tools

        return {
            "id": test_case["id"],
            "question": question[:60] + "..." if len(question) > 60 else question,
            "category": test_case["category"],
            "expected_tool": expected_tool,
            "actual_tools": actual_tools,
            "passed": passed,
            "answer_preview": final_answer[:100] + "..." if len(final_answer) > 100 else final_answer,
        }

    except Exception as e:
        return {
            "id": test_case["id"],
            "question": question[:60],
            "category": test_case["category"],
            "expected_tool": expected_tool,
            "actual_tools": [],
            "passed": False,
            "answer_preview": f"ERROR: {str(e)[:80]}",
        }


def print_results(results: list[dict]) -> None:
    """Print a formatted summary table of evaluation results."""
    # Header
    print("\n" + "=" * 100)
    print("ATHENA AGENT — ROUTING EVALUATION")
    print("=" * 100)
    print(f"\n{'ID':>3} | {'Category':<10} | {'Expected':<18} | {'Actual':<25} | {'Pass':>4} | Question")
    print("-" * 100)

    # Results
    for r in results:
        status = "✅" if r["passed"] else "❌"
        actual = ", ".join(r["actual_tools"]) if r["actual_tools"] else "(none)"
        print(
            f"{r['id']:>3} | {r['category']:<10} | {r['expected_tool']:<18} | "
            f"{actual:<25} | {status:>4} | {r['question']}"
        )

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    accuracy = (passed / total * 100) if total > 0 else 0

    print("-" * 100)
    print(f"\nOverall Accuracy: {passed}/{total} ({accuracy:.1f}%)")

    # Per-category breakdown
    categories = set(r["category"] for r in results)
    for cat in sorted(categories):
        cat_results = [r for r in results if r["category"] == cat]
        cat_passed = sum(1 for r in cat_results if r["passed"])
        cat_acc = (cat_passed / len(cat_results) * 100) if cat_results else 0
        print(f"  {cat:<10}: {cat_passed}/{len(cat_results)} ({cat_acc:.1f}%)")

    print()


def main():
    """Run the full evaluation suite."""
    print("Loading test cases...")
    test_cases = load_test_cases()
    print(f"Found {len(test_cases)} test cases.\n")

    print("Running evaluation (this may take a minute)...\n")
    results = []
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i}/{len(test_cases)}] {tc['question'][:50]}...")
        result = evaluate_single_case(tc)
        results.append(result)

    print_results(results)

    # Save results for reference
    results_path = Path(__file__).parent / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()
