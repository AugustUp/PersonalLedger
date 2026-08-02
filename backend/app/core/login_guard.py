"""登录失败防护（单 worker 内存实现）。

连续 N 次登录失败（同用户名+IP）后锁定一段时间，防止暴力破解。
部署为单 worker（SQLite 约束），内存计数足够；进程重启后计数清零，
可接受（锁定窗口很短）。
"""
import threading
import time

MAX_ATTEMPTS = 5          # 10 分钟内最多失败次数
WINDOW_SECONDS = 600      # 计数窗口 / 锁定时长（秒）

_lock = threading.Lock()
_records: dict[str, list[float]] = {}


def _key(username: str, ip: str | None) -> str:
    return f"{username.lower()}|{ip or ''}"


def is_locked(username: str, ip: str | None) -> tuple[bool, int]:
    """返回 (是否锁定, 剩余秒数)。"""
    now = time.time()
    k = _key(username, ip)
    with _lock:
        times = [t for t in _records.get(k, []) if now - t < WINDOW_SECONDS]
        if len(times) >= MAX_ATTEMPTS:
            remain = WINDOW_SECONDS - int(now - times[0])
            return True, max(1, remain)
        _records[k] = times  # 顺带清理过期记录
        return False, 0


def record_failure(username: str, ip: str | None) -> None:
    now = time.time()
    k = _key(username, ip)
    with _lock:
        times = [t for t in _records.get(k, []) if now - t < WINDOW_SECONDS]
        times.append(now)
        _records[k] = times


def reset(username: str, ip: str | None) -> None:
    with _lock:
        _records.pop(_key(username, ip), None)
