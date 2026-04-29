#!/usr/bin/env python3
"""
GenericAgent 官方更新检查脚本
对比 origin/main (官方) 与 yeelght/dev (你的分支) 的新提交

用法:
    python check_upstream.py           # 检查更新
    python check_upstream.py --merge   # 检查 + 合并官方更新到你的分支
    python check_upstream.py --log     # 只看上次更新日志
"""
import subprocess, os, json, sys
from datetime import datetime

GA_ROOT = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(GA_ROOT, ".git", "upstream_check_state.json")
YOUR_BRANCH = "yeelght/dev"
UPSTREAM_BRANCH = "origin/main"

os.chdir(GA_ROOT)

def run(cmd, capture=True):
    r = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    return r.stdout.strip() if capture else r

def color(s, code):
    return f"\033[{code}m{s}\033[0m"

import sys
# Force UTF-8 output for Windows console
if sys.stdout.encoding and sys.stdout.encoding.upper() != "UTF-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except:
        pass

def info(s):   print(f"[i] {s}")
def ok(s):     print(f"[OK] {s}")
def warn(s):   print(f"[!] {s}")
def err(s):    print(f"[X] {s}")
def hl(s):     print(f"[*] {s}")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    args = [a.lower() for a in sys.argv[1:]]
    
    if "--log" in args:
        state = load_state()
        if state.get("last_log"):
            print("=== 上次更新日志 ===")
            print(state["last_log"])
        else:
            info("暂无上次更新日志")
        return

    info("GenericAgent 官方更新检查")
    info(f"你的分支: {YOUR_BRANCH}")
    info(f"官方分支: {UPSTREAM_BRANCH}")
    print()
    
    # Step 1: fetch upstream
    info("正在拉取官方更新...")
    r = run("git fetch origin")
    if r and "error" in r.lower():
        err(f"拉取失败: {r}")
        return
    ok("拉取完成")
    
    # Step 2: compare branches
    info("正在对比分支差异...")
    
    behind = run(f"git rev-list --count {YOUR_BRANCH}..{UPSTREAM_BRANCH}")
    if not behind or behind == "0":
        ok("你的分支与官方同步！没有新更新")
        return
    
    detailed_log = run(f"git log {YOUR_BRANCH}..{UPSTREAM_BRANCH} --no-merges --pretty=format:'%h %ai %an%n  %s%n'")
    
    print()
    print("═" * 50)
    hl(f"官方有 {behind} 个新提交待查看！")
    print()
    print("=== 更新日志 ===")
    print(detailed_log)
    print()
    print("═" * 50)
    print("想合并官方更新到你的分支，请运行:")
    print("  python check_upstream.py --merge")
    print()
    
    # Save state
    save_state({
        "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_commit_count": int(behind),
        "last_log": detailed_log
    })
    
    # Step 3: optional merge
    if "--merge" in args:
        info(f"正在合并官方更新到 {YOUR_BRANCH} ...")
        
        # Check for uncommitted changes
        status = run("git status --porcelain")
        if status:
            warn("你有未提交的修改，正在暂存...")
            run("git stash push -m 'auto-stash before upstream merge'")
        
        r = run(f"git merge {UPSTREAM_BRANCH} --no-edit")
        if "merge" not in r.lower() or "conflict" in r.lower():
            if "conflict" in r.lower() or "failed" in r.lower():
                err("合并冲突！请手动解决:")
                print("  1. git status 查看冲突文件")
                print("  2. 手动解决冲突后: git add . && git commit")
                print(f"  3. git push myfork {YOUR_BRANCH}")
            else:
                ok("合并成功！")
                info("正在推送到你的 fork...")
                run(f"git push myfork {YOUR_BRANCH}", capture=False)
                ok(f"已推送到 myfork/{YOUR_BRANCH}")
                
                # Restore stash
                stash_list = run("git stash list")
                if "auto-stash before upstream merge" in stash_list:
                    run("git stash pop")
                    ok("已恢复你的本地修改")
        else:
            ok("合并成功！")
            info("正在推送到你的 fork...")
            run(f"git push myfork {YOUR_BRANCH}", capture=False)
            ok(f"已推送到 myfork/{YOUR_BRANCH}")
            
            stash_list = run("git stash list")
            if "auto-stash before upstream merge" in stash_list:
                run("git stash pop")
                ok("已恢复你的本地修改")
    
    print()
    info("提示: 再次检查请运行 python check_upstream.py")

if __name__ == "__main__":
    main()