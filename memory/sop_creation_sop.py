#!/usr/bin/env python3
"""SOP创建工具：根据任务需求生成SOP模板"""
import textwrap
from datetime import datetime
from pathlib import Path

MEM_DIR = Path(__file__).parent

TEMPLATE = textwrap.dedent("""# {title}

## 目标
{goal}

## 前置条件
{preconditions}

## 步骤
{steps}

## 输出标准
{output_criteria}

## 创建日期
{date}
""")

def create_sop(name: str, title: str, goal: str,
               steps: list, preconditions: str = "",
               output_criteria: str = "完成所有步骤") -> Path:
    """创建SOP.md文件"""
    steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    content = TEMPLATE.format(
        title=title, goal=goal, preconditions=preconditions,
        steps=steps_text, output_criteria=output_criteria,
        date=datetime.now().strftime('%Y-%m-%d')
    )
    path = MEM_DIR / f"{name}_sop.md"
    path.write_text(content, encoding='utf-8')
    return path
