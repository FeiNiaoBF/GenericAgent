"""Scheduler wrapper - starts agentmain in reflect mode for scheduler"""
import subprocess, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
subprocess.run([sys.executable, 'agentmain.py', '--reflect', 'reflect/scheduler.py'], cwd=BASE)