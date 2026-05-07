# Memory Scanner SOP (v1.0)

## 1. 快速开始
内存特征搜索工具，支持 Hex (CE 风格) 和 字符串匹配。特别提供 LLM 模式，方便大模型分析内存上下文。

## 执行摘要（≥1步执行前必读）
① 选模式(Hex/Str/LLM)→② 定位目标进程PID→③ 执行扫描特征码→④ 分析上下文 → 🛑 过验证门禁

**Python 调用方式:**
```python
import sys
sys.path.append('../memory') # 直接挂载工具目录
from procmem_scanner import scan_memory

# 示例：搜索特定 Hex 特征码，开启 llm_mode 以获取上下文
results = scan_memory(pid, "48 8b ?? ?? 00", mode="hex", llm_mode=True)
```

**CLI:**
```powershell
# 基础搜索
python ../memory/procmem_scanner.py <PID> "pattern" --mode string

# LLM 增强模式（输出包含上下文的 JSON，推荐）
python ../memory/procmem_scanner.py <PID> "pattern" --llm
```

## 2. 典型场景：结构体或关键数据定位
1. 确定目标数据的前导特征或已知常量（如特定的 Header 或 Magic Number）。
2. 在目标进程中搜索该特征：
   `scan_memory(pid, "4D 5A 90 00", mode="hex", llm_mode=True)`
3. 分析返回的 JSON 中 `context` 字段，查看目标地址前后的原始字节及 ASCII 预览。

## 3. 注意事项
- **权限**: 并非强制要求管理员权限，但需具备对目标进程的 `PROCESS_QUERY_INFORMATION` 和 `PROCESS_VM_READ` 权限。
- **效率**: 搜索大块内存时，尽量提供更唯一的特征码以减少误报。

## 4. CE式差集扫描定位动态字段
定位微信等自绘UI中随操作变化的内存字段（如当前会话标题）。核心：一次全量scan + 多次ReadProcessMemory筛选。

## 🛑 验证门禁（执行前/后强制检查）

| 检查项 | 状态 |
|--------|------|
| 目标进程PID正确？ | |
| 权限(PROCESS_VM_READ)具备？ | |
| 特征码唯一(减少误报)？ | |
| 扫描结果已分析上下文？ | |

最终裁定：`VERDICT: PASS` / `VERDICT: FAIL`
