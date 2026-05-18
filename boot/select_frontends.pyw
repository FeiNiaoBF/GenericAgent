#!/usr/bin/env python3
"""Tkinter frontend selector for GenericAgent boot launcher.

Outputs a comma-separated list of selected frontend keys to stdout.
Exit code:
  0: confirmed selection (possibly empty)
  1: cancelled or failed
"""
from __future__ import annotations

import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "boot_config.json"


def load_bots() -> list[dict[str, object]]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    bots = data.get("bots", {})
    result: list[dict[str, object]] = []
    for key, cfg in bots.items():
        if not isinstance(cfg, dict):
            continue
        entry = str(cfg.get("entry") or "")
        result.append(
            {
                "key": str(key),
                "name": str(cfg.get("name") or key),
                "enabled": bool(cfg.get("enabled")),
                "entry": entry,
                "kind": classify_frontend(str(key), entry),
            }
        )
    return result


def classify_frontend(key: str, entry: str) -> str:
    entry_l = entry.replace("\\", "/").lower()
    key_l = key.lower()
    if key_l in {"tg", "fs"}:
        return "后台服务"
    if key_l == "gui" or entry_l.endswith("launch.pyw"):
        return "GA 主桌面入口"
    if key_l == "desktop" or "qtapp.py" in entry_l:
        return "Qt 桌面前端"
    if "tuiv2" in key_l or "tui" in entry_l:
        return "终端 TUI 前端"
    if "streamlit" in key_l or "stapp.py" in entry_l:
        return "Web/Streamlit 前端"
    return "前端/服务"


def main() -> int:
    try:
        bots = load_bots()
    except Exception as exc:  # GUI entrypoint: show a visible error.
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("GenericAgent 启动选择", str(exc))
        return 1

    selected: list[str] | None = None
    root = tk.Tk()
    root.title("GenericAgent 启动项选择")
    root.geometry("620x720")
    root.minsize(560, 680)

    title = tk.Label(root, text="这次要启动哪些 GenericAgent 组件？", font=("Microsoft YaHei UI", 14, "bold"))
    title.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))

    hint = tk.Label(
        root,
        text="勾选只影响本次启动，不会改写 config/boot_config.json。GUI 是主桌面；Desktop 是旧 Qt 前端；TUI 是终端前端。",
        fg="#555",
        wraplength=560,
        justify="left",
    )
    hint.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(2, weight=1)

    list_frame = tk.Frame(root)
    list_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 4))

    vars_by_key: dict[str, tk.BooleanVar] = {}
    columns = max(1, (len(bots) + 1) // 2)
    for col in range(columns):
        list_frame.grid_columnconfigure(col, weight=1, uniform="frontend_options")

    for idx, bot in enumerate(bots):
        key = str(bot["key"])
        name = str(bot["name"])
        var = tk.BooleanVar(value=False)
        vars_by_key[key] = var

        row = idx // columns
        col = idx % columns
        cb = tk.Checkbutton(
            list_frame,
            text=f"{name}\n({key})",
            variable=var,
            anchor="center",
            justify="center",
            font=("Microsoft YaHei UI", 10),
            padx=4,
            pady=6,
        )
        cb.grid(row=row, column=col, sticky="nsew", padx=3, pady=4)

    def set_all(value: bool) -> None:
        for var in vars_by_key.values():
            var.set(value)

    def confirm() -> None:
        nonlocal selected
        selected = [key for key, var in vars_by_key.items() if var.get()]
        root.destroy()

    def cancel() -> None:
        root.destroy()

    btns = tk.Frame(root)
    btns.grid(row=3, column=0, sticky="ew", padx=18, pady=(6, 12))
    tk.Button(btns, text="全选", command=lambda: set_all(True), width=10).pack(side="left")
    tk.Button(btns, text="全不选", command=lambda: set_all(False), width=10).pack(side="left", padx=8)
    tk.Button(btns, text="取消", command=cancel, width=10).pack(side="right")
    tk.Button(btns, text="启动所选", command=confirm, width=12).pack(side="right", padx=8)

    root.protocol("WM_DELETE_WINDOW", cancel)
    root.mainloop()

    if selected is None:
        return 1
    print(",".join(selected), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
