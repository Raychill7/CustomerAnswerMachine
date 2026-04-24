# E-commerce Customer Service Agent

基于 `Python + FastAPI + DeepSeek` 的电商客服 Agent，包含对话编排、RAG 预留、工单闭环、测试评测和基础监控，适合作为简历工程化项目。

## 功能
- 多轮客服对话接口：`POST /chat`
- 人工工单接口：`POST /ticket`
- 健康检查与指标：`GET /healthz`、`GET /metrics`
- 网页演示入口：`GET /`（内置聊天页面）
- 意图识别路由：物流、退换货、发票、人工转接、知识问答
- DeepSeek API 客户端封装（重试、超时、错误映射）

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
