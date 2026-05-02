"""Scheduler wrapper - starts agentmain in reflect mode for scheduler"""
import subprocess, sys, os, json
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOT_CONFIG = os.path.join(BASE, 'boot_config.json')
SCHED_LOG = os.path.join(BASE, 'sche_tasks', 'scheduler.log')
TEMPLATE = {
    "scheduler": {
        "enabled": True,
        "script": "reflect/scheduler.py",
        "port": 50123
    }
}

# --- 启动诊断+自愈 ---
diag = {}

# 1) boot_config.json检查
diag['boot_config'] = 'OK' if os.path.exists(BOOT_CONFIG) else 'MISSING'
if diag['boot_config'] == 'MISSING':
    print(f"[run_scheduler] boot_config.json MISSING, auto-healing...")
    try:
        with open(BOOT_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(TEMPLATE, f, indent=2)
        diag['boot_config'] = 'HEALED'
        print(f"[run_scheduler] boot_config.json auto-created -> {BOOT_CONFIG}")
    except Exception as e:
        print(f"[run_scheduler] FAILED to create boot_config.json: {e}")
        diag['boot_config'] = f'HEAL_FAIL:{e}'

# 2) 检查scheduler进程（端口占用 = 已运行）
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port_open = sock.connect_ex(('127.0.0.1', TEMPLATE['scheduler']['port'])) == 0
sock.close()
diag['scheduler_already'] = 'RUNNING' if port_open else 'NOT_RUNNING'

# 3) 统计sche_tasks下的任务数
tasks_dir = os.path.join(BASE, 'sche_tasks')
task_count = 0
if os.path.isdir(tasks_dir):
    task_count = len([f for f in os.listdir(tasks_dir) if f.endswith('.json')])
diag['tasks'] = task_count

# 输出诊断
diag_str = f"boot_config={diag['boot_config']} scheduler={diag['scheduler_already']} tasks={diag['tasks']}"
print(f"[run_scheduler] Startup diagnostic: {diag_str}")

# 写入scheduler日志
try:
    os.makedirs(os.path.dirname(SCHED_LOG), exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(SCHED_LOG, 'a', encoding='utf-8') as lf:
        lf.write(f'{ts} START run_scheduler: {diag_str}\n')
except Exception as e:
    print(f"[run_scheduler] Failed to write log: {e}")

# 启动scheduler
os.chdir(BASE)
subprocess.run([sys.executable, 'agentmain.py', '--reflect', 'reflect/scheduler.py'], cwd=BASE)