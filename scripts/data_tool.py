#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本地数据工具：概览 / 导出 / 迁移打包（SQLite）。

用法（在 ops-ledger 根目录执行）：
    python scripts/data_tool.py overview                 # 列出所有表、行数、字段
    python scripts/data_tool.py export --out data/export # 全量导出 SQL + JSON 到目录
    python scripts/data_tool.py pack --out data/migrate  # 打迁移包(datetime.zip)：db快照+uploads+说明

说明：
- 数据在 data/ops_ledger.db（WAL 模式）。服务运行时本工具也可安全执行：
  概览/导出用只读连接（自动读到 WAL 最新数据），打包用 sqlite3 backup 一致性快照。
- 迁移到目标机（如统信 UOS）：解压迁移包 → 停服 → 用包内 snapshot.db 替换
  data/ops_ledger.db，把 uploads/ 覆盖到部署目录，按 README 说明重启即可。
"""
import argparse
import json
import os
import sqlite3
import sys
import zipfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.config import settings  # noqa: E402


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def db_file() -> str:
    """定位数据库文件：优先 settings 解析结果，其次项目根 data/ 下的常规位置。"""
    url = settings.database_url
    candidates = []
    if url.startswith("sqlite:///"):
        candidates.append(os.path.abspath(url.replace("sqlite:///", "", 1)))
    candidates.append(os.path.join(PROJECT_ROOT, "data", "ops_ledger.db"))
    for c in candidates:
        if os.path.exists(c):
            return c
    # 都找不到时返回 settings 解析的路径（用于明确报错）
    return candidates[0]


def upload_dir() -> str:
    return os.path.abspath(settings.upload_dir)


def _connect_ro() -> sqlite3.Connection:
    path = db_file().replace(os.sep, "/")
    conn = sqlite3.connect(f"file:///{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_names(conn) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def overview() -> None:
    conn = _connect_ro()
    print(f"数据库: {db_file()}\n")
    print(f"{'表名':<26}{'行数':>10}  字段")
    print("-" * 90)
    for t in _table_names(conn):
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        cols = [c[1] for c in conn.execute(f'PRAGMA table_info("{t}")').fetchall()]
        print(f"{t:<26}{n:>10}  {', '.join(cols)}")
    conn.close()


def export(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    conn = _connect_ro()

    # 1) 全量 SQL（schema + INSERT，可在任何 SQLite 上原样导入）
    sql_path = os.path.join(out_dir, "full_dump.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- ops-ledger 全量导出\n")
        f.write(f"-- 时间: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        f.write(f"-- 数据库: {db_file()}\n\n")
        for line in conn.iterdump():
            f.write(line + "\n")
    print(f"[OK] SQL 全量导出: {sql_path}")

    # 2) 每表一个 JSON（便于本地查询/核对）
    json_dir = os.path.join(out_dir, "json")
    os.makedirs(json_dir, exist_ok=True)
    for t in _table_names(conn):
        rows = [dict(r) for r in conn.execute(f'SELECT * FROM "{t}"').fetchall()]
        p = os.path.join(json_dir, f"{t}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        print(f"[OK] {t}.json ({len(rows)} 行)")
    conn.close()


def pack(out_dir: str, keep_uploads: bool = True) -> str:
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(out_dir, f"migrate_{stamp}.zip")

    # 一致性快照（服务运行中也可安全执行）
    snap = os.path.join(out_dir, f"snapshot_{stamp}.db")
    src = sqlite3.connect(db_file())
    dst = sqlite3.connect(snap)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    up = upload_dir()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(snap, arcname="snapshot.db")
        if os.path.isdir(up):
            n = 0
            for root, _, files in os.walk(up):
                for f in files:
                    p = os.path.join(root, f)
                    z.write(p, arcname=os.path.join("uploads", os.path.relpath(p, up)))
                    n += 1
            print(f"[OK] 已包含 {n} 个上传文件")
        else:
            print("[WARN] 未发现 uploads 目录，仅打包数据库")
        readme = _readme_text()
        z.writestr("README_迁移说明.txt", readme)

    # 清理临时快照（本机安全删除钩子可能拦截，忽略失败即可）
    try:
        os.remove(snap)
    except OSError:
        pass
    print(f"[OK] 迁移包: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")
    return zip_path


def _readme_text() -> str:
    return f"""ops-ledger 数据迁移包
=====================
生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}
来源数据库: {db_file()}

内容:
  snapshot.db  - 数据库一致性快照（含全部台账/用户/部门/日志）
  uploads/     - 附件文件（如有）

迁移步骤（Windows -> 目标服务器，如统信 UOS）:
  1) 将本压缩包上传到目标服务器
  2) 停止目标服务: bash scripts/stop.sh
  3) 备份目标现有库(可选): cp data/ops_ledger.db data/ops_ledger.db.bak
  4) 解压替换: 把 snapshot.db 覆盖为 data/ops_ledger.db
     把 uploads/ 内容覆盖到部署目录的 uploads/
  5) 启动服务: bash scripts/start.sh
  6) 用原账号登录验证数据

注意:
  - 目标机后端版本应与导出端一致（或执行 alembic upgrade head 后再导入）
  - 若跨版本且 schema 有变，建议用 full_dump.sql 方式导入而非直接替换 db
"""


def main():
    ap = argparse.ArgumentParser(description="本地数据工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("overview", help="列出所有表/行数/字段")
    ex = sub.add_parser("export", help="全量导出 SQL + JSON")
    ex.add_argument("--out", default="data/export", help="输出目录")
    pk = sub.add_parser("pack", help="打迁移包 zip")
    pk.add_argument("--out", default="data/migrate", help="输出目录")
    args = ap.parse_args()

    if args.cmd == "overview":
        overview()
    elif args.cmd == "export":
        export(args.out)
    elif args.cmd == "pack":
        pack(args.out)


if __name__ == "__main__":
    main()
