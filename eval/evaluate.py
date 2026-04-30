import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agent.graph import CustomerServiceAgent


def _safe_div(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def compute_metrics(data: list[dict], agent: CustomerServiceAgent, retrieval_k: int = 3) -> dict:
    total = len(data)
    intent_hit = 0
    recall_hit = 0
    citation_hit = 0
    citation_total = 0
    by_difficulty: dict[str, dict[str, int]] = {}

    for row in data:
        query = row["query"]
        expected_intent = row["expected_intent"]
        difficulty = row.get("difficulty", "unknown")
        expected_sources = row.get("expected_sources", [])

        intent, _ = agent.detect_intent(query)
        chunks = agent.retriever.retrieve(query, top_k=retrieval_k)
        retrieved_sources = [chunk.source for chunk in chunks]
        references = [chunk.source for chunk in chunks if chunk.score >= 0.5]

        if intent == expected_intent:
            intent_hit += 1
            by_difficulty.setdefault(difficulty, {"total": 0, "intent_hit": 0})
            by_difficulty[difficulty]["intent_hit"] += 1
        else:
            by_difficulty.setdefault(difficulty, {"total": 0, "intent_hit": 0})

        by_difficulty[difficulty]["total"] += 1

        if expected_sources:
            matched = len(set(expected_sources) & set(retrieved_sources))
            recall_hit += 1 if matched > 0 else 0
            citation_hit += len(set(expected_sources) & set(references))
            citation_total += len(set(references))

    by_difficulty_metrics = {
        name: {
            "total": bucket["total"],
            "intent_hit": bucket["intent_hit"],
            "intent_accuracy": _safe_div(bucket["intent_hit"], bucket["total"]),
        }
        for name, bucket in by_difficulty.items()
    }

    return {
        "total": total,
        "intent_hit": intent_hit,
        "intent_accuracy": _safe_div(intent_hit, total),
        f"recall_at_{retrieval_k}": _safe_div(recall_hit, sum(1 for row in data if row.get("expected_sources"))),
        "citation_precision": _safe_div(citation_hit, citation_total),
        "by_difficulty": by_difficulty_metrics,
    }


def run_eval() -> None:
    data = json.loads(Path("eval/dataset.json").read_text(encoding="utf-8"))
    agent = CustomerServiceAgent()
    metrics = compute_metrics(data, agent, retrieval_k=3)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_eval()
