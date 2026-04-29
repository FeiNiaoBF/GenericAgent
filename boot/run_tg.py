"""
Custom TG bot entry point — sets up paths and runs official frontends/tgapp.py.
Usage: python boot/run_tg.py  (or pythonw for background)
"""
import sys, os

_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
_frontends = os.path.join(_project_root, 'frontends')

# Ensure tgapp can find its module dependencies
for p in [_project_root, _frontends]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Self-contained: add .venv site-packages for direct pythonw usage
_venv_sp = os.path.join(_project_root, '.venv', 'Lib', 'site-packages')
if os.path.isdir(_venv_sp) and _venv_sp not in sys.path:
    sys.path.insert(0, _venv_sp)

# Run official tgapp
import runpy
tgapp_path = os.path.join(_frontends, 'tgapp.py')
print(f"[boot/run_tg] Running tgapp from {tgapp_path}")
runpy.run_path(tgapp_path, run_name='__main__')  
