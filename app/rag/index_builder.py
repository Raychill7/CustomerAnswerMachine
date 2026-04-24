import json
from pathlib import Path


def build_demo_index(output_path: str = "data/knowledge/faq.json") -> None:
    records = [
        {"id": "faq_shipping", "text": "物流一般在48小时内发货，支持订单号追踪。"},
        {"id": "faq_return", "text": "签收后7天内可申请退货，商品需保持完好。"},
        {"id": "faq_invoice", "text": "可在订单详情页申请电子发票，支持企业抬头。"},
    ]
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build_demo_index()
