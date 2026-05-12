#!/usr/bin/env python3
"""后台任务管理：启动/停止/监控前台和后台任务"""
import subprocess, time, psutil
from pathlib import Path

PID_DIR = Path(__file__).parent / '..' / 'temp' / 'pids'
PID_DIR.mkdir(parents=True, exist_ok=True)

def start_task(name: str, cmd: list) -> int:
    """启动后台任务"""
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (PID_DIR / f"{name}.pid").write_text(str(proc.pid))
    return proc.pid

def stop_task(name: str) -> bool:
    """停止后台任务"""
    pid_file = PID_DIR / f"{name}.pid"
    if not pid_file.exists():
        return False
    pid = int(pid_file.read_text())
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(timeout=5)
        pid_file.unlink()
        return True
    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
        pid_file.unlink(missing_ok=True)
        return False

def list_tasks() -> list:
    """列出运行中的后台任务"""
    tasks = []
    for f in PID_DIR.glob("*.pid"):
        pid = int(f.read_text())
        alive = psutil.pid_exists(pid)
        tasks.append({"name": f.stem, "pid": pid, "alive": alive})
    return tasks
