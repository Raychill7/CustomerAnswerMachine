# E-commerce Customer Service Agent

基于 `Python + FastAPI + DeepSeek` 的电商客服 Agent，包含可观测对话编排、RAG 检索增强、工单闭环、离线评测与线上失败回流机制。

## 功能
- 多轮客服对话接口：`POST /chat`
- 失败样本池接口：`GET /chat/failure-cases`
- 人工工单接口：`POST /ticket`
- 健康检查与指标：`GET /healthz`、`GET /metrics`
- 网页演示入口：`GET /`（内置聊天页面）
- 意图识别路由：物流、退换货、发票、人工转接、知识问答
- DeepSeek API 客户端封装（重试、超时、错误映射）
- 检索链路埋点：记录检索来源、分数、改写 query 与检索模式
- 混合检索：关键词匹配 + 轻量语义相似融合打分
- Query Rewrite：原 query + 改写 query 双路召回融合
- 阈值过滤与重排增强：减少低相关上下文注入噪声
- 内置演示订单数据：1 个客户 + 3 个订单（`2026001/2026002/2026003`）

## 最近更新（RAG 精进）
- **检索可观测性**：增加 `agent_trace` 结构化埋点，输出 `retrieval_debug`、`rewritten_query`、`retrieval_mode`。
- **检索能力升级**：`SimpleRetriever` 从单一路由升级为“关键词 + 语义融合 + 重排 + min_score 过滤”。
- **评测升级**：`eval/evaluate.py` 新增 `intent_accuracy`、`recall_at_k`、`citation_precision`、按难度分层统计。
- **评测数据集扩充**：`eval/dataset.json` 扩展到 120 条，包含 `easy/medium/hard` 与 `expected_sources`。
- **线上失败回流**：自动识别低置信、转人工、无引用样本并入库 `failure_cases`，用于后续人工标注和回灌评测集。
- **演示数据增强**：新增 `customers/orders` 表并在启动时幂等初始化演示订单，便于现场演示订单状态查询。

## 演示订单数据
系统启动时会自动初始化一个演示客户（`CUST-2026-DEMO`）和以下订单：
- `2026001`: `已送达`
- `2026002`: `已发货`
- `2026003`: `未发货`

你可以在聊天中直接输入订单号触发查询，例如：
- “帮我查一下订单 `2026001`”
- “订单 `2026003` 现在什么状态”

## 快速开始
1. 创建虚拟环境并安装依赖：
   - `pip install -r requirements.txt`
2. 复制环境变量：
   - `copy .env.example .env`（Windows）
3. 设置 `.env` 中的 `DEEPSEEK_API_KEY`
4. 启动服务：
   - `uvicorn app.main:app --reload`
5. 浏览器访问：
   - `http://127.0.0.1:8000/`

## 示例请求
```powershell
$bodyObj = @{ session_id="s1"; user_id="u1"; user_message="我想申请退货" }
$bodyJson = $bodyObj | ConvertTo-Json -Compress
$bodyUtf8 = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/chat" -ContentType "application/json; charset=utf-8" -Body $bodyUtf8
```

## 测试与评测
- 单元测试：`pytest`
- 规则评测：`python eval/evaluate.py`
- 压测：`locust -f tests/load_test_locust.py --host=http://127.0.0.1:8000`

### 评测输出说明
`python eval/evaluate.py` 默认输出：
- `intent_accuracy`: 意图识别准确率
- `recall_at_3`: 检索召回命中率（基于 `expected_sources`）
- `citation_precision`: 引用精度
- `by_difficulty`: `easy/medium/hard` 分层统计

## 线上失败回流机制
### 触发条件
- `confidence < FAILURE_CONFIDENCE_THRESHOLD`（默认 `0.75`）
- `intent == handoff_human`
- `intent == knowledge_qa` 且无 `references`

### 数据流
1. 用户请求命中 `POST /chat`
2. 系统自动判定是否失败样本
3. 命中则写入 `failure_cases` 待标注池
4. 通过 `GET /chat/failure-cases` 拉取样本做人工标注
5. 标注后回灌 `eval/dataset.json` 持续迭代

### 查询示例
```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/chat/failure-cases?status=new&limit=20"
```

### 相关配置
可在 `.env` 中配置：
- `FAILURE_CONFIDENCE_THRESHOLD`（默认 `0.75`）
- `FAILURE_POOL_DEFAULT_LIMIT`（默认 `50`）

## 项目结构
- `app/main.py`: FastAPI 入口
- `app/api/`: Chat/Ticket/Health API
- `app/agent/`: 意图识别与工具编排
- `app/llm/`: DeepSeek 客户端
- `app/rag/`: 检索与索引构建
- `app/db/`: 数据模型与仓储
- `tests/`: 单测与压测脚本
- `eval/`: 离线评测集与脚本
- `docs/architecture.md`: 架构说明
