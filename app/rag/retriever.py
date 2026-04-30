from dataclasses import dataclass
from math import sqrt


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
        self.keyword_aliases = {
            "shipping": {"物流", "快递", "发货", "配送", "包裹", "轨迹", "单号", "追踪"},
            "return": {"退货", "退款", "换货", "售后", "签收", "退钱"},
            "invoice": {"发票", "开票", "报销", "票据", "抬头", "税号", "凭证"},
        }
        self.doc_labels = {
            "faq_shipping": "shipping",
            "faq_return": "return",
            "faq_invoice": "invoice",
        }

    def _keyword_score(self, query: str, content: str, label: str) -> float:
        score = 0.0
        for token in self.keyword_aliases[label]:
            if token in query:
                score += 0.2
            if token in content:
                score += 0.05
        if query.lower() in content.lower():
            score += 0.2
        return score

    def _query_concept_vector(self, query: str) -> dict[str, float]:
        vector = {label: 0.0 for label in self.keyword_aliases}
        for label, aliases in self.keyword_aliases.items():
            for token in aliases:
                if token in query:
                    vector[label] += 1.0
        return vector

    @staticmethod
    def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
        dot = sum(left[k] * right[k] for k in left)
        left_norm = sqrt(sum(v * v for v in left.values()))
        right_norm = sqrt(sum(v * v for v in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _dominant_label(query_vector: dict[str, float]) -> str | None:
        label, score = max(query_vector.items(), key=lambda item: item[1])
        return label if score > 0 else None

    def retrieve(self, query: str, top_k: int = 2, min_score: float = 0.0) -> list[RetrievedChunk]:
        query_vector = self._query_concept_vector(query)
        dominant_label = self._dominant_label(query_vector)
        scored: list[RetrievedChunk] = []
        for source, content in self.docs:
            label = self.doc_labels[source]
            keyword_score = self._keyword_score(query, content, label)
            doc_vector = {name: 1.0 if name == label else 0.0 for name in self.keyword_aliases}
            semantic_score = self._cosine_similarity(query_vector, doc_vector)
            fused_score = (keyword_score * 0.6) + (semantic_score * 0.4)
            rerank_boost = 0.15 if dominant_label == label else 0.0
            final_score = fused_score + rerank_boost
            if final_score < min_score:
                continue
            scored.append(RetrievedChunk(content=content, source=source, score=final_score))
        return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
