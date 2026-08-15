# 后端模块

- `routes/`：HTTP API，仅负责参数和响应。
- `modules/`：面试、评测和情绪业务逻辑。
- `db/`：关系数据库访问。
- `GraphBase/`：Neo4j 与知识图谱。
- `utils/`：模型、语音、配置和爬虫等基础能力。
- `tools/`：文件和媒体辅助工具。

从项目根目录 `E:\view` 启动开发服务：

```bash
pip install -r server/requirements.txt
python -m server
```

PyCharm 运行配置使用：

- 运行类型：Python
- 运行目标：模块名称
- 模块名称：`server`
- 工作目录：`E:\view`
