# 自主行动 SOP

⚠️ **路径警告**：autonomous_reports 在 temp/ 下，用`./autonomous_reports/`访问，**不是**`../memory/autonomous_reports/`或`../autonomous_reports/`！TODO在cwd下。
报告存于 `./autonomous_reports/`，文件名 `RXX_简短描述.md`（XX从 history.txt 推断自增）。

授权你进行自主行动，只要不对环境造成副作用都可进行。

## 启动（第一步）
- **上下文检测**：若 `Current turn > 10`（长session），先调 `update_working_checkpoint` 压缩无效上下文，避免推理膨胀（GA Ch11 预算30k token）
- update_working_checkpoint: `自主行动｜收尾时重读SOP | from autonomous_operation_sop.helper import *; complete_task(tasktitle, historyline, report_path) 已内置TODO标记`

第二步：
```python
from autonomous_operation_sop.helper import *
print(get_history(40))  # 了解历史避免重复
print(get_todo())       # 查看待办
```

## 任务选择
- 有未完成条目 → 取**一条**，直接进入执行，其他条目下次执行
- 无 TODO → 读 `autonomous_operation_sop/task_planning.md` 规划，下次执行
- 不连续两次选相同子任务
- 价值公式：**「AI训练数据无法覆盖」×「对未来协作有持久收益」**

## 执行
- 选定任务后 update_working_checkpoint，将选中的TODO条目和执行注意事项 append 到 checkpoint 中
- **[AUTO] 模式**：`<summary>` 可简写为 `[AUTO]` 或跳过（节省token预算），但正常对话必须保留
- 调用code_run追加收尾回调: `script` 为 `helper._done_hooks.append("重读自主任务sop，检查收尾是否正确")`，`inline_eval=True`
- ≤30回合，小步快跑，边探测边实验
- 用临时脚本验证假设；禁只读即下结论，完整验证再写报告
- 即使失败也记录实验过程和结果，失败报告同样有价值
- 用户不在线，遇到需要决策的问题写入报告待审，不要卡住

**收尾（3件事缺一不可）**：
0. 重读本sop
1. 在cwd写报告（文件名任意），若有记忆更新建议，附在报告末尾
2. `from autonomous_operation_sop.helper import *; complete_task(tasktitle, historyline, report_path)` → 自动编号+移报告+写历史+**已内置TODO标记**（无需单独调set_todo）
3. 收尾后手动执行 `_done_hooks` 中的校验项 → 结束，剩余TODO留到下次再做

## 权限边界
- 无需批准：只读探测、cwd内写操作/脚本实验
- 需写入报告待审：修改 global_mem / memory下SOP、安装软件、外部API调用、删除非临时文件
- 绝对禁止：读取密钥、修改核心代码库、不可逆危险操作

## §6 规则优先级（GA Ch9 原子性）
当多条规则冲突时，按以下优先级裁决：
1. 绝对禁止项 > 2. 用户明确指令 > 3. Safety边界 > 4. SOP流程 > 5. 效率惯例
例：用户指令与SOP冲突时以用户为准；但绝对禁止项（如改ga.py核心源码）不受任何优先级覆盖。

## 等待用户审查
- 用户归来后审查报告，决定批准、修改或拒绝方案