# 运维智能台账系统 (Ops Ledger)

基于 **FastAPI + SQLite + Vue 3 + TypeScript** 的运维台账系统，适用于内网部署，已在
**统信 UOS（Debian 系）** 上验证。覆盖四类台账：

- 会议调试台账
- IP/MAC 资产台账（含变更历史）
- 批量账号台账（批次 + 明细 + 批量结果 + 导入导出）
- 通用维护台账

并包含用户/角色权限（RBAC）、部门、附件、操作日志、首页统计等支撑模块。

---

## 1. 技术栈与目录结构

```
ops-ledger/
├── backend/                # FastAPI 后端
│   ├── app/                # 应用代码 (core/models/schemas/services/api/utils)
│   ├── alembic/            # 数据库迁移
│   ├── scripts/seed.py     # 初始化管理员
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # Vue 3 + TS 前端
│   └── src/
│       ├── api/            # 接口封装 (http.ts / types.ts / index.ts)
│       ├── stores/         # Pinia (user)
│       ├── utils/          # format / permission
│       ├── layouts/        # MainLayout
│       ├── components/     # StatusTag / AttachmentManager
│       ├── router/         # 路由 + 权限守卫
│       └── views/          # 各台账页面
├── deploy/                 # 部署相关
│   ├── systemd/ops-ledger.service
│   ├── nginx/ops-ledger.conf
│   └── scripts/            # backup.sh / restore_test.sh / seed.sh
└── data/                   # SQLite 数据库 (运行时生成)
```

---

## 2. 生产目录约定（统信 UOS）

```
/opt/ops-ledger/
├── backend/            # 后端代码
├── frontend/dist/      # 前端构建产物
├── venv/               # Python 虚拟环境
├── data/ops_ledger.db  # SQLite 数据库 (WAL)
├── uploads/            # 附件
├── backups/            # 备份
├── logs/               # 日志
├── config/.env         # 生产环境变量
└── scripts/            # 运维脚本
```

---

## 3. 部署前准备（统信 UOS）

```bash
# 1) 安装依赖
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx sqlite3

# 2) 前端构建需要 Node.js (>= 18)
#    可从官网下载 Node 18+ 的 Linux 包，或 apt 安装 nodejs/npm

# 3) 创建专用低权限用户与目录
sudo useradd -r -s /usr/sbin/nologin opsledger
sudo mkdir -p /opt/ops-ledger/{backend,frontend/dist,venv,data,uploads,backups,logs,config,scripts}
```

---

## 4. 后端部署

```bash
# 拷贝代码
sudo cp -r backend/* /opt/ops-ledger/backend/
sudo cp -r frontend/dist/* /opt/ops-ledger/frontend/dist/

# 创建虚拟环境并安装依赖
sudo -u opsledger python3 -m venv /opt/ops-ledger/venv
sudo -u opsledger /opt/ops-ledger/venv/bin/pip install -r /opt/ops-ledger/backend/requirements.txt

# 生产环境变量
sudo cp /opt/ops-ledger/backend/.env.example /opt/ops-ledger/config/.env
sudo nano /opt/ops-ledger/config/.env   # 务必修改 SECRET_KEY 与 CORS_ORIGINS

# 数据库迁移（首次为空库，会自动建表）
sudo -u opsledger /opt/ops-ledger/venv/bin/alembic -c /opt/ops-ledger/backend/alembic.ini upgrade head

# 初始化管理员 (默认 admin / admin123)
sudo -u opsledger bash /opt/ops-ledger/scripts/seed.sh
```

---

## 5. systemd 开机自启

```bash
sudo cp /opt/ops-ledger/deploy/systemd/ops-ledger.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ops-ledger
sudo systemctl status ops-ledger        # 应包含 active (running)
journalctl -u ops-ledger -f              # 查看日志
```

> ⚠️ SQLite 必须保持 **单 Uvicorn worker**（`--workers 1`）。多进程写 SQLite 会显著增加锁冲突。

---

## 6. Nginx 反向代理

```bash
sudo cp /opt/ops-ledger/deploy/nginx/ops-ledger.conf /etc/nginx/conf.d/ops-ledger.conf
sudo nginx -t && sudo systemctl reload nginx
```

浏览器访问 `http://<服务器地址>/` 即可打开前端。

---

## 7. 前端本地开发 / 构建

```bash
cd frontend
npm install
npm run dev      # 本地开发 http://localhost:5173 （Vite 代理 /api -> :8000）
npm run build    # 产物输出到 frontend/dist/，拷贝到 /opt/ops-ledger/frontend/dist/
```

---

## 8. 备份与恢复演练

```bash
# 每日备份（建议 crontab: 0 2 * * *）
bash /opt/ops-ledger/scripts/backup.sh

# 每季度恢复演练（手册 17.4）
bash /opt/ops-ledger/scripts/restore_test.sh
```

备份采用 SQLite `backup` API（在线、不长时间锁写），并打包 `uploads/` 目录，保留 30 天。

---

## 9. 角色与权限

| 角色 | 说明 |
|------|------|
| `admin` 系统管理员 | 全部权限：用户、部门、日志、所有台账、备份 |
| `manager` 运维管理员 | 查看/创建/修改/导入/导出/查看历史/统计 |
| `operator` 普通运维 | 在授权范围内新增、查看、修改；**无**用户管理与日志查看权限 |

权限点示例：`meeting:view/create/update/delete/export`、`network_asset:view/create/update/import/export/history`、
`account_batch:view/create/update/import/export/delete`、`maintenance:view/create/update/delete/export`、
`system:user_manage/department_manage/log_view/backup_manage`。

前端通过路由守卫 + `v-permission` 指令控制页面与按钮显示；**后端在每个接口再次校验权限**。

---

## 10. 发布检查清单（手册附录 D）

- [ ] 代码已合并到发布分支并标记版本
- [ ] `requirements.txt` 与 `package-lock.json` 已锁定
- [ ] 数据库与附件已备份
- [ ] Alembic 迁移已在数据库副本验证（`alembic upgrade head`）
- [ ] 生产 `.env` 权限正确（600）且无默认密钥
- [ ] 前端 API 地址与 Nginx 配置正确
- [ ] FastAPI 仅使用 1 个 worker
- [ ] 上传目录与数据目录属主/权限正确（`opsledger`）
- [ ] 管理员初始密码已修改
- [ ] 登录/查询/新增/修改/导入/导出/附件/日志均通过冒烟测试
- [ ] 恢复步骤与回滚版本已记录

---

## 11. 默认账号

- 用户名 `admin`，密码 `admin123`（首次登录后请立即在「系统管理 → 用户管理」修改密码）
