#!/usr/bin/env python3
"""技能发现：扫描可用工具/函数，发现新能力"""
import inspect, pkgutil
import memory  # GA的记忆模块

def scan_module(module_name: str) -> list:
    """扫描模块中可调用的函数"""
    try:
        mod = __import__(module_name)
        funcs = [(n, f) for n, f in inspect.getmembers(mod, inspect.isfunction)
                 if not n.startswith('_')]
        return [n for n, _ in funcs]
    except ImportError:
        return []

def discover_new_skills() -> list:
    """发现memory模块下新增的工具函数"""
    known = set(dir(memory))
    # 扫描子模块
    discovered = []
    for imp, modname, ispkg in pkgutil.iter_modules(memory.__path__):
        if modname not in known:
            discovered.append(modname)
    return discovered

def report_skills() -> str:
    """输出技能报告"""
    funcs = scan_module('memory')
    new = discover_new_skills()
    report = f"📦 当前技能数: {len(funcs)}\n"
    if new:
        report += f"✨ 新发现: {', '.join(new)}"
    return report
