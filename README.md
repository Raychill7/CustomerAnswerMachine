# E-commerce Customer Service Agent

基于 `Python + FastAPI + DeepSeek` 的电商客服 Agent，包含可观测对话编排、RAG 检索增强、工单闭环、离线评测与线上失败回流机制。

## 功能
- 多轮客服对话接口：`POST /chat`
- 失败样本池接口：`GET /chat/failure-cases`
- 人工工单接口：`POST /ticket`
- 健康检查与指标：`GET /healthz`、`GET /metrics`
- 网页演示入口：`GET /`（内置聊天页面）
- 意图识别路由：物流、退换货、发票、人工转接、知识问答
- 会话记忆：按 `session_id` 从 `chat_logs` 读取最近若干轮对话，注入 LLM（知识问答、发票检索、转人工等走模型的路径），支持轮数/字符上限与按意图过滤
- DeepSeek API 客户端封装（重试、超时、错误映射）
- 检索链路埋点：记录检索来源、分数、改写 query 与检索模式
- 混合检索：关键词匹配 + 轻量语义相似融合打分
- Query Rewrite：原 query + 改写 query 双路召回融合
- 阈值过滤与重排增强：减少低相关上下文注入噪声
- 内置演示订单数据：1 个客户 + 3 个订单（`2026001/2026002/2026003`）

## 最近更新（会话记忆）
- **多轮上下文**：`POST /chat` 在调用 DeepSeek 前，将同一 `session_id` 下近期 user/assistant 轮次拼入 `messages`（system → 历史 → 当前轮结构化 payload）。
- **成本控制**：`chat_history_max_turns` 限制轮数，`chat_history_max_chars` 限制历史文本体量；`chat_history_db_fetch_limit` 控制单次从库中读取条数。
- **可选意图过滤**：`chat_history_filter=intent_related` 时优先保留与当前/上一轮意图一致的记录，无命中时回退最近少量轮次，避免无关历史噪声。
- **实现位置**：`app/db/repositories.py`（`get_recent_chat_turns`）、`app/agent/chat_history.py`（裁剪与过滤）、`app/agent/graph.py`（组装 messages）。

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

### 订单状态查询行为（避免臆测订单号）
为解决「只说查订单却被当成某一固定单号」的问题，编排按下面优先级处理（意图仍为 `order_status`，评测脚本中的 `detect_intent` 不变）：

1. **消息里带有订单号（`20` + 5 位数字）**  
   调用 `query_order_status` 读库；若不存在则明确回复「未找到订单」，**不再**编造在途状态。
2. **明确要查「自己的订单」但未给单号**（例如包含「查询订单」「查订单」「订单状态」「我的订单」或「查…订单」类表述）  
   - 若请求里带了已映射的演示 `user_id`，则列出该演示客户在库中的订单，请用户回复要查哪一单；  
   - 若无映射用户或未绑定演示客户数据，则提示用户补充订单号。  
   演示环境下，`POST /chat` 的 `user_id` 与演示客户 `CUST-2026-DEMO` 的映射为：`demo-user`、`u1`（见 `app/agent/graph.py` 中的 `_CHAT_USER_TO_DEMO_CUSTOMER`）。网页演示默认使用 `demo-user`。
3. **其余命中物流/订单关键词但不属于上述「点名查自己的单」**  
   视为泛化的物流/时效类问题，走 **RAG 检索 + LLM**（与知识问答相同的检索链路），避免在没有单号时调用订单详情工具。

实现要点：`app/agent/graph.py`（分流与话术）、`app/db/repositories.py`（`list_orders_for_customer`）、`app/agent/tools.py`（未知订单 `ok=False` + `not_found`）。

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

## 会话记忆配置
走 LLM 的回复会带上同一 `session_id` 的近期对话；订单状态、纯退换货模板等**不调用模型**的路径不受此项影响。

可在 `.env` 中配置（亦对应 `app/core/config.py` 中的字段名）：
- `CHAT_HISTORY_MAX_TURNS`（默认 `12`）：注入模型的最多历史轮数（每轮含一条 user + 一条 assistant）。
- `CHAT_HISTORY_MAX_CHARS`（默认 `8000`）：历史对话文本（不含 system 与当前轮 payload）的字符上限，从更早轮次向前裁剪。
- `CHAT_HISTORY_FILTER`（默认 `all`）：`all` 使用裁剪后的全部意图历史；`intent_related` 按当前/上一轮意图筛选后再裁剪。
- `CHAT_HISTORY_DB_FETCH_LIMIT`（默认 `48`）：每次请求从 `chat_logs` 最多读取的行数，供内存侧筛选与截断。

## 项目结构
- `app/main.py`: FastAPI 入口
- `app/api/`: Chat/Ticket/Health API
- `app/agent/`: 意图识别与工具编排（含 `chat_history.py` 会话裁剪）
- `app/llm/`: DeepSeek 客户端
- `app/rag/`: 检索与索引构建
- `app/db/`: 数据模型与仓储
- `tests/`: 单测与压测脚本
- `eval/`: 离线评测集与脚本
- `docs/architecture.md`: 架构说明
