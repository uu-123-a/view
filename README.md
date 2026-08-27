# view — 多模态 AI 模拟面试平台

`view` 是一个面向求职者的全栈 AI 模拟面试系统。项目使用 React、TypeScript、Vite 和 Flask 构建，通过浏览器摄像头、麦克风、文本对话、情绪反馈与面试报告完成沉浸式面试训练，不依赖预先下载的数字人视频素材。

系统已接入讯飞星火大模型，并提供本地 `faster-whisper` 语音识别、MySQL 业务数据持久化、管理员独立身份库、模型降级策略、接口限流和自动化安全测试。

## 在线体验

- 正式环境：<https://view-production-e7f7.up.railway.app>
- 健康检查：<https://view-production-e7f7.up.railway.app/api/health>

线上服务运行在 Railway。首次访问或平台重新部署时可能需要等待数秒。

## 核心功能

### AI 模拟面试

- 按目标岗位、难度、面试类型和重点技能创建面试。
- 浏览器摄像头实时预览，无需数字人视频文件。
- 支持文字回答和麦克风录音回答。
- 讯飞星火动态生成题目、追问和回答评价。
- 星火不可用时自动切换到本地题库和本地评价，避免页面白屏。
- 自动记录面试时长、问题、回答、评价和模型来源。

### 报告与训练

- 生成综合评分、优势、改进建议和逐题复盘。
- 提供回答情绪分析、情绪时间线和训练建议。
- 支持复盘笔记、错题本及错题重新作答。
- 根据薄弱项生成学习与训练计划。

### 求职辅助

- 岗位浏览、岗位收藏和投递状态管理。
- PDF、DOCX、TXT 简历解析与 AI 分析。
- 针对目标岗位给出简历优化建议。
- 职业助手多轮对话。
- 求职日程、通知中心和知识图谱。

### 用户与管理后台

- 普通用户注册、登录、退出和个人资料维护。
- 管理员使用独立登录入口和独立身份数据库。
- 管理题库、岗位、系统开关、用户概况和运行事件。
- 普通用户不能访问管理接口，管理员会话也不会自动获得普通用户数据权限。

## 技术架构

| 层级 | 技术与职责 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite、Recharts、Lucide React |
| 后端 | Python 3.12+、Flask、Gunicorn/Waitress |
| 大模型 | 讯飞星火 WebSocket API，失败时使用本地降级逻辑 |
| 语音 | 浏览器录音 + 本地 `faster-whisper` 转写 |
| 数据库 | MySQL：`view` 业务库、`view_admin` 管理员身份库 |
| 测试 | Python `unittest`、TypeScript 类型检查、Playwright E2E |
| 部署 | Docker 多阶段构建、Railway、健康检查和自动重启 |

生产构建中，Vite 先生成 `dist/`，随后 Flask 同时提供前端静态文件与 `/api` 接口，因此公网环境只需要部署一个 Web 服务。

## 项目目录

```text
view/
├─ src/
│  ├─ app/                   页面与应用布局
│  │  ├─ admin/             管理后台
│  │  ├─ auth/              登录与注册
│  │  ├─ careers/           岗位、投递、日程
│  │  ├─ growth/            简历、知识图谱、职业助手
│  │  ├─ home/              首页仪表盘
│  │  ├─ interview/         面试设置、面试房间、报告与情绪
│  │  └─ records/           历史记录、错题、通知、个人中心
│  ├─ features/             可复用业务功能
│  ├─ services/             前端 API 封装
│  ├─ utils/                语音等通用逻辑
│  └─ styles.css            全局视觉与页面背景
├─ server/
│  ├─ routes/               Flask HTTP API
│  ├─ modules/              面试、评测、情绪、星火、Whisper 服务
│  ├─ db/                   Repository、MySQL 兼容层与建表脚本
│  ├─ GraphBase/            知识图谱能力
│  ├─ tools/                迁移、备份、恢复与测试工具
│  ├─ tests/                后端单元与权限安全测试
│  ├─ app.py                Flask 应用工厂
│  ├─ production.py         生产 WSGI 入口
│  └─ security.py           安全响应头和接口限流
├─ e2e/                     Playwright 浏览器测试
├─ scripts/                 前端构建辅助脚本
├─ Dockerfile               Railway/容器构建文件
├─ railway.json             Railway 构建及健康检查配置
├─ start-production.ps1     Windows 本机生产启动脚本
└─ DEPLOYMENT.md            补充部署说明
```

## 环境要求

- Node.js 20 或更高版本，推荐 Node.js 22。
- npm 10 或更高版本。
- Python 3.12 或更高版本。
- MySQL 8.0。
- 支持摄像头和麦克风的现代浏览器。
- 使用摄像头和麦克风时，公网地址必须启用 HTTPS；`localhost` 开发环境可直接使用。

## 安装项目

在 PyCharm 中打开项目根目录 `E:\view`，然后在 PyCharm 底部的 Terminal 执行：

```powershell
cd E:\view
npm.cmd install
python -m pip install -r server\requirements.txt
```

建议在 PyCharm 中为项目创建独立虚拟环境，并确认 Python Interpreter 指向该环境。

## 配置环境变量

复制配置模板：

```powershell
Copy-Item server\.env.example server\.env
```

修改 `server\.env`：

```dotenv
MOSS_ENV=development
MOSS_SECRET_KEY=请替换为至少32位随机字符串
MOSS_COOKIE_SECURE=false
MOSS_TRUST_PROXY=false

DATABASE_ENGINE=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=view
MYSQL_ADMIN_DATABASE=view_admin
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码

SPARKAI_URL=wss://spark-api.xf-yun.com/v3.1/chat
SPARKAI_APP_ID=
SPARKAI_API_SECRET=
SPARKAI_API_KEY=
SPARKAI_DOMAIN=generalv3

WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

不要把真实密码、星火密钥或生产会话密钥写入 README、提交到 Git，或放在前端 `src/` 中。`server/.env` 已被 Git 忽略；生产环境应通过 Railway Variables 配置。

### 生成生产会话密钥

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

将结果设置为 `MOSS_SECRET_KEY`。生产环境必须至少为 32 个字符。

## 初始化 MySQL

先在 MySQL 或 Navicat 中创建两个数据库：

```sql
CREATE DATABASE IF NOT EXISTS view
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS view_admin
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

当 `DATABASE_ENGINE=mysql` 且 `MYSQL_AUTO_INIT=true` 时，Flask 启动会读取 `server/db/schema_mysql.sql` 并自动创建缺失的数据表。

数据库职责：

- `view`：普通用户、面试、报告、简历、岗位、投递、训练等业务数据。
- `view_admin`：管理员身份和管理员登录数据。

Navicat 只是数据库管理客户端，不需要额外“同步”。只要 Navicat 与项目连接到同一个 MySQL 地址和端口，就能看到项目写入的数据；看不到新表时，右键数据库并选择“刷新”。

## 开发环境启动

需要同时运行后端和前端。

### 终端一：启动 Flask

```powershell
cd E:\view
python -m server
```

后端地址：<http://127.0.0.1:5000>

### 终端二：启动 Vite

```powershell
cd E:\view
npm.cmd run dev
```

前端地址：<http://localhost:5173>

Vite 会把 `/api` 自动代理到 `127.0.0.1:5000`。浏览器第一次使用面试功能时，需要允许摄像头和麦克风权限。

### PyCharm 运行配置

后端可创建一个 Python 运行配置：

- Run kind：Module name
- Module name：`server`
- Working directory：`E:\view`
- Python interpreter：安装过 `server/requirements.txt` 的解释器

前端可以继续在 Terminal 中运行 `npm.cmd run dev`。

## 本机生产模式

Windows 可直接执行：

```powershell
cd E:\view
.\start-production.ps1
```

脚本会构建前端，并用 Waitress 在 `127.0.0.1:8000` 启动整个应用：

- 应用：<http://127.0.0.1:8000>
- 健康检查：<http://127.0.0.1:8000/api/health>

## 讯飞星火模型

星火模型用于动态生成面试题和追问、评价回答、生成报告、分析和优化简历、职业助手对话及错题重答评价。

密钥只由后端 `server/modules/spark_service.py` 从环境变量读取，不会发送到浏览器。网络异常、配置缺失或星火接口失败时，面试模块会回退到本地题库与本地评价，前端仍应保持可用。

## 本地 Whisper 语音识别

录音由浏览器生成 WAV 文件，再发送到后端本地 Whisper 服务转写。首次使用时可能需要下载模型，因此会比后续调用慢。

默认 CPU 配置：

```dotenv
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

服务器内存较小时可改用 `tiny` 或 `base`。Railway 等轻量实例需要评估内存和模型下载时间；若资源不足，可暂时关闭语音识别，仅保留文本回答。

## 接口限流与安全

```dotenv
MOSS_LOGIN_RATE_LIMIT=10
MOSS_LOGIN_RATE_WINDOW_SECONDS=300
MOSS_MODEL_RATE_LIMIT=30
MOSS_MODEL_RATE_WINDOW_SECONDS=60
```

- 登录限流按客户端 IP 和登录接口分别统计。
- 大模型限流按用户和具体模型接口分别统计。
- 超限返回 HTTP `429`、`Retry-After` 响应头和 `retry_after` 字段。
- 当前计数保存在单个 Python 进程内，适用于当前 Railway 单实例部署。
- 扩展到多个 Web 实例前，应将限流状态迁移到 Redis。

后端还默认设置 CSP、`X-Frame-Options`、`X-Content-Type-Options`、Referrer Policy 和浏览器权限策略等安全响应头。

## 测试与质量检查

完整测试：

```powershell
npm.cmd run test:all
```

分项执行：

```powershell
npm.cmd run test:types
npm.cmd run test:backend
npm.cmd run build
npm.cmd run test:e2e
```

后端测试工具会强制使用隔离的 SQLite 测试环境，不会连接或修改生产 MySQL。测试覆盖健康检查、认证、面试流程、模型降级、情绪分析、接口限流、角色权限隔离和跨用户防越权。

## Railway 部署

仓库已提供 `Dockerfile` 与 `railway.json`。推荐部署结构：

1. Railway Web Service 连接 GitHub 仓库的 `main` 分支。
2. Railway 项目内创建 MySQL 服务。
3. Web Service Variables 引用 MySQL 服务变量。
4. 配置生产变量：

```dotenv
MOSS_ENV=production
MOSS_COOKIE_SECURE=true
MOSS_TRUST_PROXY=true
MOSS_SECRET_KEY=至少32位随机字符串
DATABASE_ENGINE=mysql
MYSQL_AUTO_INIT=true
MYSQL_DATABASE=view
MYSQL_ADMIN_DATABASE=view_admin
```

5. 再配置星火变量和可选的 Whisper 变量。
6. 部署后访问 `/api/health`，确认返回：

```json
{"service":"moss-view","status":"ok"}
```

`railway.json` 使用 Dockerfile 构建项目，并通过 `/api/health` 完成健康检查。容器内 Gunicorn 使用 1 个 worker 和 4 个线程，以兼容当前进程内限流设计。

## 数据备份和迁移

备份正式业务库与管理员库：

```powershell
python server\tools\backup_mysql.py
```

从旧 SQLite 数据构建 MySQL 候选库：

```powershell
python server\tools\migrate_sqlite_runtime_to_mysql.py
python server\tools\promote_mysql_runtime.py --confirm
```

数据库迁移和提升操作会修改数据，执行前务必创建备份并确认目标数据库名称。

## 常见问题

### 页面白屏

先检查浏览器开发者工具 Console，再检查后端终端或 Railway Logs，并执行：

```powershell
npm.cmd run test:types
npm.cmd run build
```

星火服务失败不应直接导致白屏；白屏通常是前端运行时错误、旧缓存或前后端版本不一致。

### 摄像头无法使用

- 确认浏览器已授予摄像头权限。
- 关闭正在占用摄像头的其他程序。
- 公网环境必须使用 HTTPS。
- Windows 设置中确认允许桌面应用访问摄像头。

### 麦克风或语音识别无法使用

- 确认浏览器麦克风权限和系统输入设备。
- 至少录音 1 秒。
- 查看后端是否已成功加载 Whisper 模型。
- 服务器资源不足时先使用文本回答。

### Flask 显示 development server 警告

这是开发模式提示，不是运行错误。本地开发可以忽略；生产环境应使用项目中的 Gunicorn、Waitress 或 Docker 配置。

### PyCharm 中 import 出现红线

确认工作目录为 `E:\view`，Python Interpreter 已安装依赖，并使用模块方式启动：

```powershell
python -m server
```

必要时将项目根目录标记为 Sources Root，然后让 PyCharm 重新索引。

## 安全注意事项

- 不要提交 `.env`、数据库密码、星火密钥、会话密钥或备份文件。
- 不要让 MySQL `3306` 直接暴露到公网。
- 生产环境必须启用 HTTPS 和安全 Cookie。
- 定期备份 `view` 和 `view_admin`，并验证备份可恢复。
- 定期轮换第三方 API 密钥和管理员密码。
- 公开测试前应先清理自动化测试账号和测试面试记录。

## 相关文档

- [部署说明](DEPLOYMENT.md)
- [后端模块说明](server/README.md)
- [环境变量模板](server/.env.example)

## License

当前仓库未声明开源许可证。除非仓库所有者另行授权，否则默认保留全部权利。
