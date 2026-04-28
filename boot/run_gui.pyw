"""
One-click GUI launcher — sets up paths and runs launch.pyw (Streamlit + webview).
Usage: pythonw boot/run_gui.pyw [--tg] [--feishu] [--qq] [--dingtalk] [--wecom] [--sched]
       Double-click .pyw to open GUI window with no console.
"""
import sys, os

_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)

# Ensure imports work
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Add .venv site-packages for pythonw compatibility
_venv_sp = os.path.join(_project_root, '.venv', 'Lib', 'site-packages')
if os.path.isdir(_venv_sp) and _venv_sp not in sys.path:
    sys.path.insert(0, _venv_sp)

# Run launch.pyw — it handles argparse, webview, idle monitor, and optional bot subprocesses
import runpy

_launch_path = os.path.join(_project_root, 'launch.pyw')
print(f"[boot/run_gui] Launching GenericAgent GUI from {_launch_path}")
runpy.run_path(_launch_path, run_name='__main__')