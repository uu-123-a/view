# view 正式部署说明

## 当前完成状态

项目已经达到“本机生产模式可部署”状态：前端产物由 Flask 提供，Waitress 负责 WSGI 服务，生产日志、安全响应头、登录限流、MySQL 双库和自动备份均已配置。

## Windows 本机生产运行

在 PowerShell 中执行：

```powershell
cd E:\view
python -m pip install -r server\requirements.txt
npm.cmd install
.\start-production.ps1
```

服务地址为 `http://127.0.0.1:8000`，健康检查为 `http://127.0.0.1:8000/api/health`。

## MySQL 数据库与备份

```powershell
python server\tools\backup_mysql.py
```

备份保存在 `server/backups/`，每次同时生成 `view.sql` 和 `view_admin.sql`。`view` 存放普通用户与业务数据，`view_admin` 单独存放管理员身份。

从旧 SQLite 数据重新构建候选库时执行：

```powershell
python server\tools\migrate_sqlite_runtime_to_mysql.py
python server\tools\promote_mysql_runtime.py --confirm
```

## 公网部署

1. 准备 Windows/Linux 云服务器、域名和开放的 80/443 端口。
2. 在服务器环境变量中设置 `MOSS_ENV=production`、随机 `MOSS_SECRET_KEY`，并填入新的星火密钥。
3. HTTPS 环境设置 `MOSS_COOKIE_SECURE=true`；反向代理环境设置 `MOSS_TRUST_PROXY=true`。
4. Waitress 仅监听 `127.0.0.1:8000`，由 Nginx 使用 `server/deploy/nginx-view.conf` 反向代理。
5. 使用 Certbot 或云厂商证书启用 HTTPS，再把 Waitress 注册为系统服务。

## 上线前必须人工完成

- 在讯飞控制台撤销曾经公开过的旧密钥，生成新密钥并只写入服务器 `.env`。
- 提供服务器登录方式、域名和证书方案；这些外部资源未提供前，不能安全代替用户发布到公网。
- 确认防火墙只公开 80/443，MySQL 3306 不对公网开放。

## 验收命令

```powershell
npm.cmd run test:all
Invoke-WebRequest http://127.0.0.1:8000/api/health
```
