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

## 简历可写亮点（示例）
- 设计并实现电商客服 Agent，支持业务工具调用与知识问答融合。
- 完成 LLM 接入层（超时/重试/用量统计）与统一响应协议，提升系统稳定性。
- 建立测试 + 离线评测 + 指标监控闭环，形成可复现的工程化交付流程。

## Railway 部署（网站可访问）
1. 新建 GitHub 仓库并推送本项目代码。
2. Railway 新建项目，选择该仓库。
3. 在 Railway 设置启动命令：
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. 在 Railway 环境变量中配置：
   - `DEEPSEEK_API_KEY=你的真实密钥`
   - `DEEPSEEK_BASE_URL=https://api.deepseek.com`
   - `DEEPSEEK_MODEL=deepseek-chat`
   - `CORS_ALLOW_ORIGINS=*`（生产环境建议改成你的网站域名）
5. 部署后直接访问 Railway 分配的域名即可打开聊天网页（`/`）。
