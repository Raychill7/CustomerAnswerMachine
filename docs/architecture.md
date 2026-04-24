# 电商客服 Agent 架构说明

## 架构目标
- 多轮对话可控：意图识别 + 工具调用 + LLM 生成。
- 知识问答可信：检索证据注入，支持来源返回。
- 工程可维护：配置隔离、结构化日志、测试与评测、指标采集。

## 核心流程
1. 用户请求进入 `POST /chat`。
2. Agent 先做意图识别，决定走业务工具或知识检索。
3. 将工具结果/检索片段拼装为上下文，调用 DeepSeek 生成答复。
4. 返回统一结构（answer/intent/confidence/actions/references/usage）。
5. 落库会话日志，并输出 Prometheus 指标。

## 关键模块
- `app/agent/graph.py`: 对话编排与路由。
- `app/agent/tools.py`: 订单、退货、人工工单工具。
- `app/rag/retriever.py`: 检索层（当前为轻量实现，后续可替换向量库）。
- `app/llm/deepseek_client.py`: DeepSeek API 封装，含重试/超时。
- `app/observability/metrics.py`: 统一指标定义。

## 可观测性指标
- 请求量：`http_requests_total`
- 接口延迟：`http_request_duration_seconds`
- 工具失败次数：`tool_failures_total`

## 后续增强建议
- 将 `SimpleRetriever` 升级为 Chroma/Milvus + 重排模型。
- 引入 OpenTelemetry exporter 对接 Jaeger/Tempo。
- 增加会话记忆裁剪策略与成本控制策略。
