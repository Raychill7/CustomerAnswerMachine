import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agent.graph import CustomerServiceAgent


def run_eval() -> None:
    data = json.loads(Path("eval/dataset.json").read_text(encoding="utf-8"))
    agent = CustomerServiceAgent()

    total = len(data)
    hit = 0
    for row in data:
        intent, _ = agent.detect_intent(row["query"])
        if intent == row["expected_intent"]:
            hit += 1

    accuracy = hit / total if total else 0
    print(json.dumps({"total": total, "hit": hit, "accuracy": accuracy}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_eval()
