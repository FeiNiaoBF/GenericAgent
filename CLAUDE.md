# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup

```bash
# Python 3.10 through 3.13 is supported; README recommends 3.11/3.12 for GUI compatibility.
uv pip install -e ".[ui]"
# or minimal runtime dependencies only:
pip install requests streamlit pywebview

cp mykey_template.py mykey.py
# edit mykey.py with at least one LLM config
```

`pyproject.toml` intentionally keeps dependencies minimal. Install optional frontend/bot packages only when working on that integration instead of installing everything up front:

```bash
uv pip install -e ".[all-frontends]"
pip install python-telegram-bot qq-botpy pycryptodome qrcode lark-oapi wecom-aibot-sdk dingtalk-stream
```

### Run

```bash
# CLI REPL
python agentmain.py

# Desktop Streamlit + pywebview launcher
python launch.pyw

# Streamlit UI directly
streamlit run frontends/stapp.py
streamlit run frontends/stapp2.py

# One-shot file-IO task mode; writes under temp/<task>/
python agentmain.py --task <task_id> --input "prompt text"

# Reflect mode; repeatedly calls check() in the script
python agentmain.py --reflect reflect/scheduler.py

# Launcher with optional services
python launch.pyw --tg --qq --feishu --wecom --dingtalk --sched
```

### Frontends and bridges

```bash
python frontends/tgapp.py          # Telegram, requires tg_* keys in mykey.py
python frontends/qqapp.py          # QQ, requires qq_* keys
python frontends/fsapp.py          # Feishu/Lark, requires fs_* keys
python frontends/wecomapp.py       # WeCom, requires wecom_* keys
python frontends/dingtalkapp.py    # DingTalk, requires dingtalk_* keys
python frontends/wechatapp.py      # personal WeChat bot
python frontends/qtapp.py          # Qt desktop frontend
python frontends/genericagent_acp_bridge.py --llm-no 0
```

### Validation

There is no committed test suite in this repository. For syntax/import validation, use targeted compile checks on the files you changed, for example:

```bash
python -m py_compile agentmain.py agent_loop.py ga.py llmcore.py
python -m py_compile frontends/stapp.py frontends/tgapp.py reflect/scheduler.py
```

When changing a runtime path, also run that exact entrypoint long enough to confirm startup/import success. Examples: `python agentmain.py`, `streamlit run frontends/stapp.py`, or the relevant bot script after configuring its optional dependencies and `mykey.py` values.

## Architecture

GenericAgent is a small autonomous agent runtime built around `agentmain.py`, `agent_loop.py`, `ga.py`, and `llmcore.py`.

- `agentmain.py` owns the top-level `GeneraticAgent` object. It loads LLM sessions from `mykey.py`/`mykey.json`, builds the system prompt from `assets/sys_prompt*.txt` plus memory, manages the task queue, handles slash commands such as `/session.*` and `/resume`, and exposes CLI, one-shot `--task`, and `--reflect` modes.
- `agent_loop.py` is the core turn loop. It sends messages to the active client, parses tool calls, dispatches tools through a handler, collects tool results, and decides whether to continue, exit, or ask for another prompt. It also defines hook points used by plugins and tracing.
- `ga.py` implements the tool handler (`GenericAgentHandler`) and the atomic tools: code execution, browser scan/JS execution, file read/write/patch, ask-user interruption, working checkpoints, and long-term memory update kickoff. Tool paths are resolved relative to the handler cwd, usually `temp/`.
- `llmcore.py` implements model/session backends. It supports OpenAI-compatible chat/completions and responses APIs, Anthropic Messages, native tool calling, text-protocol tool calling, prompt/cache markers, history trimming, streaming parsers, retry behavior, and `MixinSession` failover.

## Memory and prompts

The runtime memory model is layered and stored under `memory/`. `get_global_memory()` injects `memory/global_mem_insight.txt` together with `assets/insight_fixed_structure*.txt`; `agentmain.py` also creates `memory/global_mem.txt` and `memory/global_mem_insight.txt` if absent. The `start_long_term_update` tool expects `memory/memory_management_sop.md` and updates memory only after completed tasks.

`.gitignore` intentionally ignores most `memory/*`, `reflect/*`, schedules, logs, temp files, and local credentials, then whitelists selected SOP/tool files. Be careful when adding new memory, SOP, reflect, or schedule files: update the whitelist if the file should be versioned.

## LLM configuration

`mykey_template.py` is the authoritative guide for provider config. `agentmain.py` scans variables whose names contain `api`, `config`, or `cookie`, then chooses session type from the variable name:

- `native` + `claude` → `NativeClaudeSession`
- `native` + `oai` → `NativeOAISession`
- `claude` without `native` → `ClaudeSession`
- `oai` without `native` → `LLMSession`
- `mixin` → `MixinSession` failover across configured sessions

Runtime session attributes can be adjusted from the GenericAgent REPL/UI with `/session.<name>=<json-or-string>`. The whitelist lives in `agentmain.py`; non-whitelisted attributes are rejected.

## Frontend structure

`launch.pyw` starts `frontends/stapp.py` in Streamlit, wraps it in a pywebview window, and can optionally spawn bot frontends and the scheduler. `frontends/chatapp_common.py` centralizes shared chat commands (`/help`, `/status`, `/stop`, `/new`, `/restore`, `/continue`, `/llm`) and message/file formatting behavior for bot frontends.

Individual frontend scripts create a `GeneraticAgent`, start its background `run()` thread, translate inbound platform messages into `agent.put_task(...)`, and stream queue output back to the platform. Optional platform credentials and allowlists are read from `mykey.py`/`mykey.json`.

`frontends/genericagent_acp_bridge.py` exposes GenericAgent over ACP JSON-RPC on stdio. It redirects normal stdout to stderr before importing `agentmain.py` so print output cannot corrupt the JSON-RPC stream.

## Scheduling and reflect mode

`agentmain.py --reflect <script>` loads a Python script with `INTERVAL`, `ONCE`, `check()`, and optional `on_done(result)`. `reflect/scheduler.py` is the main scheduler: it scans `sche_tasks/*.json`, enforces schedule/cooldown/max-delay rules, writes completion reports under `sche_tasks/done/`, and periodically runs L4 session archive compression.

`launch.pyw --sched` starts the scheduler reflect process. `reflect/scheduler.py` uses a local port lock to avoid duplicate scheduler instances.

## Plugins and observability

Plugins are opt-in. `llmcore.reload_mykeys()` imports `plugins.langfuse_tracing` only when `langfuse_config` exists in the loaded key config. The Langfuse plugin monkey-patches logging, SSE parsers, handler tool callbacks, and the agent loop to create task, generation, and tool observations without requiring core call sites to import Langfuse directly.
