# OpenClaw 会话搜索

一个用于搜索和管理 [OpenClaw](https://github.com/openclaw/openclaw) AI 助手会话的 Web 工具。

## 功能

- 🔍 **关键字搜索** - 支持按会话关键字搜索消息内容
- 🏷️ **Agent 筛选** - 支持按 Agent 筛选
- 📋 **会话详情** - 查看会话的完整信息
- 💰 **Token 统计** - 显示总/输入/输出/缓存 Token 使用量
- 📄 **一键复制** - 复制会话消息内容到剪贴板
- 🎨 **精美 UI** - 浅色系渐变背景，现代化卡片设计

## 原理

### 数据来源

从 OpenClaw 的 agents 目录读取会话数据：

```
{AGENTS_DIR}/
├── main/
│   └── sessions/
│       ├── sessions.json      # 会话索引文件
│       └── {session_id}.jsonl # 消息记录文件
└── other agent/
```

### sessions.json 结构

每个会话包含以下字段：

- `sessionId`: 会话唯一 ID
- `key`: 会话标识符（如 `agent:main:feishu:direct:ou_xxx`）
- `totalTokens`: 总 Token 数量
- `inputTokens`: 输入 Token
- `outputTokens`: 输出 Token
- `cacheRead`: 缓存读取 Token
- `cacheWrite`: 缓存写入 Token
- `sessionFile`: 消息文件路径
- `agentId`: Agent 名称

### 消息文件格式

消息存储在 `.jsonl` 文件中，每行一个 JSON 对象，包含：

- `type`: 消息类型（message/session/model_change 等）
- `message.content`: 消息内容数组
- `message.role`: 角色（user/assistant）

### 搜索实现

1. 读取所有 Agent 的 `sessions.json`
2. 加载每个会话的消息内容
3. 在服务端进行关键字匹配
4. 返回筛选后的结果

## 配置文件

配置文件 `config.ini` 位于脚本同级目录：

```ini
[server]
host = 0.0.0.0
port = 5000

[agents]
agents_dir = C:\Users\user\.openclaw\agents
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| server.host | 服务监听地址 | 0.0.0.0 |
| server.port | 服务监听端口 | 5000 |
| agents.agents_dir | OpenClaw agents 目录 | C:\Users\user\.openclaw\agents |

## 快速开始

### 安装依赖

```bash
pip install flask
```

### 启动服务

```bash
python session_search_server.py
```

### 访问

打开浏览器访问：http://localhost:5000

## 目录结构

```
session_search/
├── session_search_server.py  # 主程序
├── config.ini               # 配置文件
└── README.md               # 说明文档
```

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML + CSS（无 JavaScript 依赖）
- **数据格式**: JSON / JSONL

## 许可证

MIT License
