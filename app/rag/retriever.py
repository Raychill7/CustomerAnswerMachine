from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    content: str
    source: str
    score: float


class SimpleRetriever:
    def __init__(self) -> None:
        self.docs = [
            ("faq_shipping", "物流一般在48小时内发货，支持订单号追踪。"),
            ("faq_return", "签收后7天内可申请退货，商品需保持完好。"),
            ("faq_invoice", "可在订单详情页申请电子发票，支持企业抬头。"),
        ]

    def retrieve(self, query: str, top_k: int = 2) -> list[RetrievedChunk]:
        query_lower = query.lower()
        scored: list[RetrievedChunk] = []
        for source, content in self.docs:
            score = 0.2
            if "退" in query and "退货" in content:
                score += 0.6
            if "物流" in query or "快递" in query:
                if "物流" in content:
                    score += 0.6
            if "发票" in query and "发票" in content:
                score += 0.6
            if query_lower in content.lower():
                score += 0.2
            scored.append(RetrievedChunk(content=content, source=source, score=score))
        return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
