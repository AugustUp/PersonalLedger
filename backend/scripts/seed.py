"""Seed an initial admin user (and optional default departments).

Run AFTER ``alembic upgrade head``:
    python -m scripts.seed
Environment:
    SEED_ADMIN_USERNAME (default: admin)
    SEED_ADMIN_PASSWORD (default: admin123  -> CHANGE BEFORE PRODUCTION)
    SEED_ADMIN_REAL_NAME (default: 系统管理员)
"""
import os

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.department import Department
from app.models.user import User


def main():
    username = os.environ.get("SEED_ADMIN_USERNAME", "admin")
    password = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")
    real_name = os.environ.get("SEED_ADMIN_REAL_NAME", "系统管理员")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            print(f"用户 {username} 已存在，跳过。")
        else:
            db.add(User(
                username=username,
                password_hash=hash_password(password),
                real_name=real_name,
                role="admin",
                is_active=True,
            ))
            db.commit()
            print(f"已创建管理员用户: {username}")

        defaults = ["信息科", "网络中心", "运维部"]
        for name in defaults:
            if not db.query(Department).filter(Department.name == name).first():
                db.add(Department(name=name))
        db.commit()
        print("默认部门已就绪。")
    finally:
        db.close()


if __name__ == "__main__":
    main()
