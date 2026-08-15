# view

`view` 是一个基于 React、TypeScript、Vite 与 Flask 的 AI 模拟面试系统。项目使用用户摄像头、对话框和网页视觉，不依赖下载数字人视频素材。

## 功能模块

- 模拟面试：岗位配置、摄像头预览、语音/文本作答、星火模型追问与降级题库。
- 面试报告：评分、反馈、复盘笔记、错题本和训练计划。
- 求职辅助：岗位中心、简历分析、投递看板、日程和职业助手。
- 用户系统：注册、登录、个人中心、普通用户与管理员隔离权限。
- 管理后台：题库、岗位、用户、系统设置和运行事件。
- 数据：MySQL `view` 是正式业务运行库，`view_admin` 是独立管理员身份库，可直接通过 Navicat 管理。

## 目录

```text
src/features/       前端按业务功能分类
server/routes/      HTTP API
server/modules/     业务服务与模型调用
server/db/          数据访问层
server/GraphBase/   知识图谱
server/utils/       语音、配置等通用能力
server/tools/       MySQL 迁移、提升和双库备份工具
server/tests/       后端自动化测试
e2e/                Playwright 浏览器测试
```

## 开发启动

在 PyCharm 中打开 `E:\view`，分别开启两个终端：

```powershell
python server\app.py
```

```powershell
npm.cmd run dev
```

浏览器访问 `http://localhost:5173`。

## 测试与生产启动

```powershell
npm.cmd run test:all
.\start-production.ps1
```

生产启动后访问 `http://127.0.0.1:8000`。公网发布步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。

> `.env` 包含私密配置，已经被 Git 忽略。请勿把真实密钥提交到仓库。
