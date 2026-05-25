# 队友社区系统对接说明

## 概述

本文档说明队友社区系统如何接入 campus-agent-service（交小伴 Agent Service），实现 AI 增强能力。

## 架构

```
[前端 (队友)]
    │
    ├──→ [社区后端 (队友)] ── 用户、帖子、任务、积分
    │
    └──→ [Agent Service (我)] ── AI Agent、帖子分析、任务草稿、安全检查
              │
              └──→ [社区后端 API] ── 创建正式任务（通过 CommunityClient 调用）
```

## ID 统一方案

为了跨系统关联数据，使用以下外部 ID 字段：

| 字段 | 含义 | 产生方 | 使用方 |
|------|------|--------|--------|
| `external_user_id` | 用户唯一标识 | 队友用户系统 | Agent Service |
| `source_post_id` | 社区帖子 ID | 队友帖子系统 | Agent Service |
| `created_task_id` | 正式任务 ID | 队友任务系统 | Agent Service |
| `points_record_id` | 积分记录 ID | 队友积分系统 | Agent Service |

Agent Service **不直接操作**队友数据库，只保存上述外部 ID 做关联。

## 队友需要提供的 API

Agent Service 通过 `CommunityClient` 调用队友社区 API：

### 1. GET /api/users/{external_user_id}
获取用户基本信息。

### 2. GET /api/posts/{post_id}
获取帖子详情。

### 3. POST /api/tasks
创建正式互助任务。

**请求体建议格式：**
```json
{
  "title": "任务标题",
  "description": "任务描述",
  "task_type": "学习辅导",
  "tags": ["高数", "辅导"],
  "source_post_id": "post_001",
  "creator_external_user_id": "user_123",
  "agent_draft_id": "draft_abc"
}
```

**响应建议格式：**
```json
{
  "task_id": "task_001",
  "status": "published"
}
```

## 调用流程示例

### 帖子转任务完整流程

```
1. 前端 → Agent Service: POST /api/community-agent/analyze-post
   传入帖子数据 → 返回 AI 分析结果

2. 前端 → Agent Service: POST /api/community-agent/convert-post-to-task
   传入帖子数据 → 返回任务草稿

3. Agent Service → 前端: 返回 draft (needs_confirmation=true)
   前端展示确认界面给用户

4. 前端 → Agent Service: POST /api/confirmations
   创建确认记录

5. 用户确认后 → Agent Service: POST /api/confirmations/resolve

6. Agent Service → 队友社区: POST /api/tasks (通过 CommunityClient)
   创建正式任务

7. Agent Service 保存 created_task_id 到 task_drafts 表
```

## 跨语言开发说明

队友可以使用任何语言（Java、Go、Node.js 等）开发社区系统，不影响产品集成：

- Agent Service 通过 **HTTP REST API** 提供服务
- 队友通过 **HTTP REST API** 提供服务给 Agent Service 调用
- 数据交换格式为 **JSON**
- ID 关联通过外部 ID 字段实现

## 环境变量配置

队友需要在 .env 中配置：

```
COMMUNITY_SERVICE_BASE_URL=http://localhost:8080/api
COMMUNITY_SERVICE_API_KEY=your_api_key
```

## 联调步骤建议

1. 双方各自本地启动服务
2. 用 curl/Postman 测试 Agent Service 接口
3. Agent Service 调用队友 API 时查看 external_api_calls 表日志
4. 确认 ID 关联正确
