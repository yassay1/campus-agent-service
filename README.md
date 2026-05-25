# 交小伴 Agent Service

校园生活智能体平台 - Agent 后端服务层。

## 项目定位

campus-agent-service 是"交小伴"平台的 **Agent 后端服务层**，通过 FastAPI 提供可调用、可测试、可联调、可展示的 Agent API 服务。

本项目**不是**完整前端项目，也**不是**完整积分互助社区平台。

## 核心原则

**LLM-driven Agent, API-constrained Execution**
（大模型驱动决策，接口约束执行）

- 大模型负责智能决策：需求理解、Agent 推荐、帖子分析、任务草稿生成、安全检查
- 后端接口负责约束执行：参数校验、权限边界、状态记录、日志存储、用户确认

## 技术栈

| 技术 | 定位 |
|------|------|
| Python + FastAPI | REST API + Swagger 文档 |
| LangChain | 真实 LLM 调用封装、Tool 调用、RAG 检索 |
| LangGraph | Agent 流程编排、状态流转 |
| PostgreSQL | Agent 数据持久化 |
| Redis | 会话临时状态、任务草稿缓存 |
| Polars | 知识库数据清洗、日志分析（不用于实时聊天） |
| Docker | 统一启动环境 |

## 我负责什么

Agent 后端服务层：私人助理 Agent、4 个专业 Agent、社区管理员 Agent、Agent 推荐、帖子分析、帖子转任务草稿、安全检查、用户确认、RAG 知识库、Agent 运行日志、Tool 调用日志、队友社区接口 client、FastAPI API、Swagger 文档、Docker 环境。

## 队友负责什么

前端页面、用户系统、社区帖子系统、评论/点赞/收藏、任务大厅、正式互助任务表、任务报名、积分系统、社区数据库、社区审核后台。

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入真实配置（特别是 LLM 参数）
```

### 2. Docker 启动（推荐）

```bash
docker-compose up -d
```

### 3. 本地开发启动

```bash
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问 Swagger

打开 http://localhost:8000/docs

## 环境变量

关键配置项（详见 .env.example）：

- `LLM_PROVIDER` — LLM 提供商
- `LLM_API_KEY` — API Key
- `LLM_API_BASE` — API 地址
- `LLM_MODEL_NAME` — 模型名称
- `POSTGRES_*` — PostgreSQL 连接信息
- `REDIS_*` — Redis 连接信息
- `COMMUNITY_SERVICE_BASE_URL` — 队友社区服务地址

## 真实 LLM 配置

本项目按真实 LLM 接入方式设计。未配置 `LLM_API_KEY`、`LLM_API_BASE` 和 `LLM_MODEL_NAME` 时，涉及大模型调用的接口会返回明确错误提示：

> "当前未配置真实 LLM 参数，无法执行 Agent 智能判断。请在 .env 中配置 LLM_API_KEY、LLM_API_BASE 和 LLM_MODEL_NAME。"

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/assistant/chat | 私人助理聊天 |
| POST | /api/agents/recommend | Agent 推荐 |
| POST | /api/agents/chat | 专业 Agent 聊天 |
| POST | /api/community-agent/analyze-post | 帖子分析 |
| POST | /api/community-agent/convert-post-to-task | 帖子转任务草稿 |
| POST | /api/safety/check | 安全检查 |
| POST | /api/confirmations | 创建确认请求 |
| POST | /api/rag/search | RAG 知识库搜索 |
| GET | /api/agent-runs/{run_id} | 查询 Agent 运行记录 |

## 项目结构

```
campus-agent-service/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── api/                  # API 路由
│   ├── agents/               # Agent 实现
│   ├── graphs/               # LangGraph 流程骨架
│   ├── chains/               # LangChain Chains
│   ├── tools/                # LangChain Tools
│   ├── schemas/              # Pydantic Schema
│   ├── db/                   # 数据模型
│   ├── services/             # 业务服务
│   ├── data_processing/      # Polars 数据处理脚本
│   └── config/               # 配置
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── docs/
```

## License

本项目为大学生创新项目。
