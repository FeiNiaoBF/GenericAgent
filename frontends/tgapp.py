import os
import sys
import threading
import asyncio
import queue as Q
from collections import deque
from difflib import SequenceMatcher
import re
import time
import uuid

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)
_TEMP_DIR = os.path.join(_PROJECT_ROOT, "temp")

from agentmain import GeneraticAgent

try:
    from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.constants import ParseMode
    from telegram.error import RetryAfter
    from telegram.ext import (
        ApplicationBuilder,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
    from telegram.request import HTTPXRequest
except Exception:
    print("Please ask the agent install python-telegram-bot to use telegram module.")
    sys.exit(1)

from chatapp_common import (
    FILE_HINT,
    HELP_TEXT,
    TELEGRAM_MENU_COMMANDS,
    clean_reply,
    ensure_single_instance,
    extract_files,
    format_restore,
    redirect_log,
    require_runtime,
)
from continue_cmd import handle_frontend_command, reset_conversation
from plan_cmd import (
    active_plan_metadata,
    build_plan_followup_prompt,
    handle_frontend_command as handle_plan_frontend,
)
from btw_cmd import handle_frontend_command as handle_btw_frontend_command
from llmcore import mykeys
from frontends.persona_pool import get_phrase, load_phrase_pool
from frontends.tg_html import (
    TELEGRAM_HTML_LIMIT,
    escape_html,
    render_for_telegram_html,
    render_for_telegram_plain_text,
    split_html_text,
)

agent = GeneraticAgent()
agent.verbose = False
agent.inc_out = True
ALLOWED = set(mykeys.get("tg_allowed_users", []))

_CHII = load_phrase_pool()

_RETRY_AFTER_MARGIN_SECONDS = 1.0
_QUEUE_WAIT_SECONDS = 1
_STREAM_UPDATE_INTERVAL_SECONDS = 2.0
_STREAM_MIN_UPDATE_CHARS = 400
_ASK_MENU_MAX_SIZE = 200
_ASK_USER_HOOK_KEY = "telegram_ask_user_menu"
_ASK_CALLBACK_PREFIX = "ask:"
_ASK_CANCEL_ACTION = "none"
_ASK_CANCEL_LABEL = "none of these above"
_ASK_CANCEL_PROMPT = "已取消选择，请直接发送下一步操作。"
_ask_menu_events = Q.Queue()
_ask_menu_store = {}
_SUMMARY_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.DOTALL)
_SUMMARY_OPEN_TAG = "<summary>"
_SUMMARY_CLOSE_TAG = "</summary>"
_SUMMARY_MIN_INTERVAL_SECONDS = 1.2
_SUMMARY_MAX_RETAINED = 3
_SUMMARY_SIMILARITY_THRESHOLD = 0.88
_SUMMARY_RECENT_WINDOW = 5
_ENABLE_TG_SUMMARIES = False
_TURN_MARKER_RE = re.compile(r"^\*{0,2}LLM Running \(Turn (\d+)\) \.\.\.\*{0,2}\s*$")
_CODE_FENCE_RE = re.compile(r"^\s*(`{3,})(.*)$")
_STICKER_EXTENSIONS = {".tgs", ".webm", ".webp"}
_NOTIFY_STICKERS = {
    "wake": {"set_name": "ChiChiStickers_by_ohchii_bot", "emoji": "😊"},
    "sleep": {"set_name": "ChiChiStickers_by_ohchii_bot", "emoji": "😴"},
}
_NOTIFY_MEDIA = {
    "wake": os.path.join(_PROJECT_ROOT, "boot", "icons", "chi (11).png"),
    "sleep": os.path.join(_PROJECT_ROOT, "boot", "icons", "chi (14).png"),
}
_NOTIFY_STICKER_CACHE = {}
_TG_EXTRA_SYSTEM_PROMPT = """
[Telegram Frontend Rules]
You are replying through Telegram.
1. `<summary>` will be rendered by the Telegram frontend as a compact summary block above the main answer.
2. Keep `<summary>` to exactly one short line, no bullets, no blank lines, no code, ideally <= 18 Chinese chars or <= 12 English words.
3. After `</summary>`, start the main answer immediately. Do not repeat the same summary sentence again in the body.
4. Do not output incomplete summary tags. Never emit bare `<summary>` or `</summary>`.
5. Telegram body must optimize for mobile readability: short paragraphs, flat bullets only when needed, avoid wide markdown tables unless essential, avoid repeated restatement.
6. Prefer concise final answers over step-by-step progress narration unless the user explicitly asks for detailed process logs.
""".strip()


def _chii(key):
    return get_phrase(key, pool=_CHII)


def _apply_tg_extra_system_prompt():
    llmclients = getattr(agent, "llmclients", []) or []
    current = getattr(agent, "llmclient", None)
    if current is not None and current not in llmclients:
        llmclients = [current] + list(llmclients)

    for client in llmclients:
        backend = getattr(client, "backend", None)
        if backend is None:
            continue
        setattr(backend, "extra_sys_prompt", _TG_EXTRA_SYSTEM_PROMPT)


async def _resolve_notify_sticker(bot, phrase_key):
    spec = _NOTIFY_STICKERS.get(phrase_key)
    if not isinstance(spec, dict):
        return None

    set_name = str(spec.get("set_name") or "").strip()
    emoji = str(spec.get("emoji") or "").strip()
    index = spec.get("index")
    cache_key = (set_name, emoji, index)
    if cache_key in _NOTIFY_STICKER_CACHE:
        return _NOTIFY_STICKER_CACHE[cache_key]

    if not set_name:
        return None

    sticker_set = await bot.get_sticker_set(set_name)
    stickers = list(getattr(sticker_set, "stickers", None) or [])
    target = None

    if emoji:
        for sticker in stickers:
            if getattr(sticker, "emoji", "") == emoji:
                target = sticker
                break

    if target is None and isinstance(index, int) and 0 <= index < len(stickers):
        target = stickers[index]

    file_id = getattr(target, "file_id", None)
    if file_id:
        _NOTIFY_STICKER_CACHE[cache_key] = file_id
    return file_id


async def _send_notify_local_media(bot, chat_id, phrase_key, text):
    media_path = _NOTIFY_MEDIA.get(phrase_key)
    if not media_path or not os.path.exists(media_path):
        return False

    media_ext = os.path.splitext(media_path)[1].lower()
    with open(media_path, "rb") as media_file:
        if media_ext in _STICKER_EXTENSIONS:
            await bot.send_sticker(chat_id=chat_id, sticker=media_file)
            await bot.send_message(chat_id=chat_id, text=text)
        else:
            await bot.send_photo(chat_id=chat_id, photo=media_file, caption=text)
    return True


async def _send_notify_event(bot, chat_id, phrase_key):
    text = _chii(phrase_key)

    try:
        sticker_file_id = await _resolve_notify_sticker(bot, phrase_key)
    except Exception as exc:
        sticker_file_id = None
        print(
            f"[{time.strftime('%m-%d %H:%M')}] TG notify sticker resolve failed for {phrase_key}: {exc}",
            flush=True,
        )

    if sticker_file_id:
        try:
            await bot.send_sticker(chat_id=chat_id, sticker=sticker_file_id)
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as exc:
                print(
                    f"[{time.strftime('%m-%d %H:%M')}] TG notify text send failed after sticker for {phrase_key}: {exc}",
                    flush=True,
                )
            return
        except Exception as exc:
            print(
                f"[{time.strftime('%m-%d %H:%M')}] TG notify sticker send failed for {phrase_key}: {exc}",
                flush=True,
            )

    try:
        if await _send_notify_local_media(bot, chat_id, phrase_key, text):
            return
    except Exception as exc:
        print(
            f"[{time.strftime('%m-%d %H:%M')}] TG notify media send failed for {phrase_key}: {exc}",
            flush=True,
        )

    await bot.send_message(chat_id=chat_id, text=text)


def _resolve_files(paths):
    files, seen = [], set()
    for fpath in paths:
        if not os.path.isabs(fpath):
            fpath = os.path.join(_TEMP_DIR, fpath)
        if fpath in seen or not os.path.exists(fpath):
            continue
        files.append(fpath)
        seen.add(fpath)
    return files


def _files_from_text(raw_text):
    cleaned = clean_reply(raw_text) if (raw_text or "").strip() else ""
    return _resolve_files(extract_files(cleaned))


def _files_from_done_item(item):
    if not isinstance(item, dict):
        return None
    files = item.get("files")
    if files is None:
        return None
    if isinstance(files, str):
        files = [files]
    if not isinstance(files, (list, tuple)):
        return []
    normalized = [str(path).strip() for path in files if str(path).strip()]
    return _resolve_files(normalized)


def _extract_completed_summaries(buffer):
    text = buffer or ""
    summaries = [
        match.group(1).strip()
        for match in _SUMMARY_RE.finditer(text)
        if match.group(1).strip()
    ]
    last_open = text.rfind(_SUMMARY_OPEN_TAG)
    last_close = text.rfind(_SUMMARY_CLOSE_TAG)
    if last_open != -1 and last_open > last_close:
        remainder = text[last_open:]
    else:
        remainder = ""
    return summaries, remainder


def _normalize_summary_key(text):
    normalized = re.sub(r"\s+", " ", text or "").strip().lower()
    normalized = re.sub(r"[`*_~<>\[\](){}|]+", "", normalized)
    return normalized


def _summary_similarity(left, right):
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    shorter, longer = sorted((left, right), key=len)
    if shorter and shorter in longer and len(shorter) / max(1, len(longer)) >= 0.72:
        return len(shorter) / max(1, len(longer))
    return SequenceMatcher(a=left, b=right).ratio()


def _line_complete(line):
    return (line or "").endswith(("\n", "\r"))


def _turn_marker_number(line):
    match = _TURN_MARKER_RE.fullmatch((line or "").strip())
    return int(match.group(1)) if match else None


def _maybe_partial_turn_marker(line):
    text = (line or "").strip().lstrip("*")
    if not text:
        return False
    marker_head = "LLM Running (Turn "
    return marker_head.startswith(text) or text.startswith(marker_head)


def _maybe_partial_code_fence(line):
    return bool(re.match(r"^\s*`{1,}[^`\r\n]*$", line or ""))


async def _send_files(root_msg, files):
    for fpath in files:
        try:
            with open(fpath, "rb") as fp:
                if fpath.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    await root_msg.reply_photo(fp)
                else:
                    await root_msg.reply_document(fp)
        except Exception:
            pass


def _is_not_modified_error(exc):
    return "not modified" in str(exc).lower()


def _extract_ask_user_event(ctx):
    exit_reason = (ctx or {}).get("exit_reason") or {}
    if exit_reason.get("result") != "EXITED":
        return None
    payload = exit_reason.get("data")
    if not isinstance(payload, dict):
        return None
    if (
        payload.get("status") != "INTERRUPT"
        or payload.get("intent") != "HUMAN_INTERVENTION"
    ):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    raw_candidates = data.get("candidates") or []
    if not isinstance(raw_candidates, (list, tuple)):
        return None

    candidates = []
    for candidate in raw_candidates:
        if candidate is None:
            continue
        text = str(candidate).strip()
        if text:
            candidates.append(text)
    if not candidates:
        return None

    question = (
        str(data.get("question") or "请选择下一步操作：").strip()
        or "请选择下一步操作："
    )
    return {"question": question, "candidates": candidates}


def _register_ask_user_hook():
    if not hasattr(agent, "_turn_end_hooks"):
        agent._turn_end_hooks = {}

    def _hook(ctx):
        event = _extract_ask_user_event(ctx)
        if event:
            _ask_menu_events.put(event)

    agent._turn_end_hooks[_ASK_USER_HOOK_KEY] = _hook


def _drain_latest_ask_user_event():
    latest = None
    while True:
        try:
            latest = _ask_menu_events.get_nowait()
        except Q.Empty:
            break
    return latest


def _build_ask_user_markup(menu_id, candidates):
    rows = [
        [
            InlineKeyboardButton(
                candidate, callback_data=f"{_ASK_CALLBACK_PREFIX}{menu_id}:{idx}"
            )
        ]
        for idx, candidate in enumerate(candidates)
    ]
    rows.append(
        [
            InlineKeyboardButton(
                _ASK_CANCEL_LABEL,
                callback_data=f"{_ASK_CALLBACK_PREFIX}{menu_id}:{_ASK_CANCEL_ACTION}",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def _parse_ask_callback_data(data):
    if not (data or "").startswith(_ASK_CALLBACK_PREFIX):
        return None, None
    payload = data[len(_ASK_CALLBACK_PREFIX) :]
    menu_id, sep, action = payload.partition(":")
    if not sep or not menu_id or not action:
        return None, None
    return menu_id, action


def _build_text_prompt(text):
    return f"{FILE_HINT}\n\n{text}"


def _plan_scope_id(update):
    chat_id = getattr(getattr(update, "effective_chat", None), "id", None)
    user_id = getattr(getattr(update, "effective_user", None), "id", None)
    return f"tg:{chat_id or 'chat'}:{user_id or 'user'}"


def _normalize_ask_menu_event(stored):
    if isinstance(stored, dict):
        candidates = stored.get("candidates") or []
        return {
            "question": str(stored.get("question") or "请选择下一步操作：").strip()
            or "请选择下一步操作：",
            "candidates": [
                str(candidate).strip()
                for candidate in candidates
                if str(candidate).strip()
            ],
        }
    if isinstance(stored, (list, tuple)):
        return {
            "question": "请选择下一步操作：",
            "candidates": [
                str(candidate).strip() for candidate in stored if str(candidate).strip()
            ],
        }
    return None


def _render_ask_user_result(event, selected=None, cancelled=False):
    question = escape_html(
        str(event.get("question") or "请选择下一步操作：").strip()
        or "请选择下一步操作："
    )
    candidates = [escape_html(c) for c in (event.get("candidates") or [])]
    lines = [question, "", "选项："]
    for idx, candidate in enumerate(candidates, start=1):
        lines.append(f"{idx}. {candidate}")
    lines.append(f"{len(candidates) + 1}. {escape_html(_ASK_CANCEL_LABEL)}")
    lines.append("")
    if cancelled:
        lines.append(f"已取消：{escape_html(_ASK_CANCEL_LABEL)}")
    elif selected:
        lines.append(f"已选择：{escape_html(selected)}")
    return "\n".join(lines)


async def _clear_ask_reply_markup(query):
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as exc:
        print(f"[TG ask_user menu cleanup] {type(exc).__name__}: {exc}", flush=True)


async def _edit_ask_user_result(query, event, selected=None, cancelled=False):
    try:
        text = _render_ask_user_result(event, selected=selected, cancelled=cancelled)
        await query.edit_message_text(
            text, parse_mode=ParseMode.HTML, reply_markup=None
        )
    except Exception as exc:
        print(f"[TG ask_user menu edit] {type(exc).__name__}: {exc}", flush=True)
        await _clear_ask_reply_markup(query)


async def _send_ask_user_menu(root_msg, event):
    menu_id = uuid.uuid4().hex[:16]
    candidates = event["candidates"]
    while len(_ask_menu_store) >= _ASK_MENU_MAX_SIZE:
        _ask_menu_store.pop(next(iter(_ask_menu_store)), None)
    _ask_menu_store[menu_id] = {
        "question": event["question"],
        "candidates": list(candidates),
    }

    try:
        question_html = escape_html(event["question"])
        await root_msg.reply_text(
            question_html,
            parse_mode=ParseMode.HTML,
            reply_markup=_build_ask_user_markup(menu_id, candidates),
        )
    except Exception as exc:
        _ask_menu_store.pop(menu_id, None)
        print(f"[TG ask_user menu error] {type(exc).__name__}: {exc}", flush=True)
        fallback = (
            render_for_telegram_plain_text(event["question"])
            + "\n"
            + "\n".join(
                f"- {render_for_telegram_plain_text(candidate)}" for candidate in candidates
            )
        )
        await root_msg.reply_text(fallback)


class _TelegramReplySession:
    def __init__(self, root_msg):
        self.root_msg = root_msg
        self.live_msg = None
        self.raw_text = ""
        self.files = []
        self.sent_segments = 0
        self.active_display = ""
        self.pending_display = ""
        self._edit_overflow_msgs = {}
        self.retry_until = 0.0
        self.active_preview_segment = ""
        self.last_stream_update_at = 0.0
        self.last_stream_raw_len = 0
        self.summary_buffer = ""
        self.can_use_summary_draft = hasattr(self.root_msg, "reply_text_draft")
        self.summary_retained_count = 0
        self.sent_summaries = set()
        self.recent_summary_keys = deque(maxlen=_SUMMARY_RECENT_WINDOW)
        self.last_summary_key = ""
        self.last_summary_draft_id = None
        self.last_summary_message = None
        self.last_summary_sent_at = 0.0

    def _now(self):
        return time.monotonic()

    def _retry_after_seconds(self, exc):
        retry_after = getattr(exc, "_retry_after", None)
        if retry_after is None:
            retry_after = getattr(exc, "retry_after", 0) or 0
        if hasattr(retry_after, "total_seconds"):
            retry_after = retry_after.total_seconds()
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            return 0.0

    def _set_retry_after(self, exc):
        wait_seconds = self._retry_after_seconds(exc) + _RETRY_AFTER_MARGIN_SECONDS
        self.retry_until = max(self.retry_until, self._now() + wait_seconds)

    def _is_retrying(self):
        return self._now() < self.retry_until

    async def _wait_for_retry(self):
        remaining = self.retry_until - self._now()
        if remaining > 0:
            await asyncio.sleep(remaining)

    async def _retry_call(self, func, *args):
        while True:
            await self._wait_for_retry()
            try:
                return await func(*args)
            except RetryAfter as exc:
                self._set_retry_after(exc)

    def _plain_text_fallback(self):
        return render_for_telegram_plain_text(self.raw_text) or "..."

    async def _reply_html_once(self, html_text):
        try:
            return await self.root_msg.reply_text(html_text, parse_mode=ParseMode.HTML)
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception:
            return await self.root_msg.reply_text(self._plain_text_fallback())

    async def _edit_html_once(self, msg, html_text):
        try:
            updated = await msg.edit_text(html_text, parse_mode=ParseMode.HTML)
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception as exc:
            if _is_not_modified_error(exc):
                return msg
            updated = await msg.edit_text(self._plain_text_fallback())
        return updated if hasattr(updated, "edit_text") else msg

    async def _edit_summary_message_once(self, msg, html_text):
        try:
            updated = await msg.edit_text(html_text, parse_mode=ParseMode.HTML)
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception as exc:
            if _is_not_modified_error(exc):
                return msg
            print(f"[TG summary edit fallback] {type(exc).__name__}: {exc}", flush=True)
            try:
                return await self.root_msg.reply_text(
                    html_text, parse_mode=ParseMode.HTML
                )
            except RetryAfter as retry_exc:
                self._set_retry_after(retry_exc)
                raise
        return updated if hasattr(updated, "edit_text") else msg

    def _make_draft_id(self):
        return max(1, int(uuid.uuid4().int % (2**31 - 1)))

    def _message_key(self, msg):
        chat_id = getattr(getattr(msg, "chat", None), "id", None)
        message_id = getattr(msg, "message_id", None)
        if chat_id is not None and message_id is not None:
            return (chat_id, message_id)
        if message_id is not None:
            return ("message", message_id)
        return ("object", id(msg))

    async def _delete_text_once(self, msg):
        delete = getattr(msg, "delete", None)
        if delete is None:
            return
        try:
            result = delete()
            if hasattr(result, "__await__"):
                await result
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception as exc:
            print(f"[TG stale overflow delete error] {type(exc).__name__}: {exc}", flush=True)

    async def _delete_text(self, msg, wait_retry=True):
        if wait_retry:
            await self._retry_call(self._delete_text_once, msg)
        else:
            await self._delete_text_once(msg)

    async def _edit_text(self, msg, text, wait_retry=True):
        segments = _markdown_safe_segments(text) or ["..."]
        old_key = self._message_key(msg)
        overflow_msgs = self._edit_overflow_msgs.get(old_key, [])
        if wait_retry:
            updated = await self._retry_call(self._edit_text_once, msg, segments[0])
        else:
            updated = await self._edit_text_once(msg, segments[0])
        primary_msg = updated if hasattr(updated, "edit_text") else msg
        self._edit_overflow_msgs.pop(old_key, None)

        new_overflow_msgs = []
        for index, segment in enumerate(segments[1:]):
            if index < len(overflow_msgs):
                overflow_msg = overflow_msgs[index]
                if wait_retry:
                    edited_overflow = await self._retry_call(self._edit_text_once, overflow_msg, segment)
                else:
                    edited_overflow = await self._edit_text_once(overflow_msg, segment)
                new_overflow_msgs.append(
                    edited_overflow if hasattr(edited_overflow, "edit_text") else overflow_msg
                )
            else:
                new_overflow_msgs.append(await self._reply_text(segment, wait_retry=wait_retry))

        for stale_msg in overflow_msgs[len(new_overflow_msgs):]:
            await self._delete_text(stale_msg, wait_retry=wait_retry)

        if new_overflow_msgs:
            self._edit_overflow_msgs[self._message_key(primary_msg)] = new_overflow_msgs
        return primary_msg

    def _summary_html(self, summary, strip_blockquotes=False):
        safe_summary = summary.replace("<_quote_>", "").replace("</_quote_>", "")
        if strip_blockquotes:
            safe_summary = safe_summary.replace("<blockquote>", "").replace(
                "</blockquote>", ""
            )
        return render_for_telegram_html(f"<_quote_>{safe_summary}</_quote_>")

    async def _send_summary_once(self, html_text):
        if self.can_use_summary_draft:
            draft_id = self._make_draft_id()
            try:
                await self.root_msg.reply_text_draft(
                    draft_id,
                    html_text,
                    parse_mode=ParseMode.HTML,
                )
                self.last_summary_draft_id = draft_id
                self.last_summary_message = None
                return None
            except RetryAfter as exc:
                self._set_retry_after(exc)
                raise
            except Exception as exc:
                print(
                    f"[TG summary draft fallback] {type(exc).__name__}: {exc}",
                    flush=True,
                )
                self.can_use_summary_draft = False
                self.last_summary_draft_id = None
        try:
            message = await self.root_msg.reply_text(
                html_text, parse_mode=ParseMode.HTML
            )
            self.last_summary_message = message
            return message
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise

    async def _replace_last_summary_once(self, html_text):
        if self.can_use_summary_draft and self.last_summary_draft_id is not None:
            try:
                await self.root_msg.reply_text_draft(
                    self.last_summary_draft_id,
                    html_text,
                    parse_mode=ParseMode.HTML,
                )
                return None
            except RetryAfter as exc:
                self._set_retry_after(exc)
                raise
            except Exception as exc:
                print(
                    f"[TG summary draft replace fallback] {type(exc).__name__}: {exc}",
                    flush=True,
                )
                self.can_use_summary_draft = False
                self.last_summary_draft_id = None
        if self.last_summary_message is not None:
            self.last_summary_message = await self._edit_summary_message_once(
                self.last_summary_message,
                html_text,
            )
            return self.last_summary_message
        return await self._send_summary_once(html_text)

    async def _wait_for_summary_slot(self):
        elapsed = self._now() - self.last_summary_sent_at
        remaining = _SUMMARY_MIN_INTERVAL_SECONDS - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)

    async def _emit_summary_list(self, summaries):
        for summary in summaries:
            key = _normalize_summary_key(summary)
            if not key or key in self.sent_summaries:
                continue
            if (
                self.last_summary_key
                and _summary_similarity(key, self.last_summary_key)
                >= _SUMMARY_SIMILARITY_THRESHOLD
            ):
                self.sent_summaries.add(key)
                if len(key) <= len(self.last_summary_key):
                    continue
                html_summary = self._summary_html(summary)
                if not html_summary:
                    continue
                await self._retry_call(self._replace_last_summary_once, html_summary)
                self.last_summary_key = key
                if self.recent_summary_keys:
                    self.recent_summary_keys[-1] = key
                else:
                    self.recent_summary_keys.append(key)
                self.last_summary_sent_at = self._now()
                continue
            if any(
                _summary_similarity(key, recent_key) >= _SUMMARY_SIMILARITY_THRESHOLD
                for recent_key in self.recent_summary_keys
            ):
                self.sent_summaries.add(key)
                continue
            self.sent_summaries.add(key)
            html_summary = self._summary_html(summary, strip_blockquotes=True)
            if not html_summary:
                continue
            await self._wait_for_summary_slot()
            reuse_last_slot = self.summary_retained_count >= _SUMMARY_MAX_RETAINED and (
                self.last_summary_draft_id is not None
                or self.last_summary_message is not None
            )
            if reuse_last_slot:
                await self._retry_call(self._replace_last_summary_once, html_summary)
            else:
                await self._retry_call(self._send_summary_once, html_summary)
                self.summary_retained_count += 1
            self.last_summary_key = key
            self.recent_summary_keys.append(key)
            self.last_summary_sent_at = self._now()

    async def emit_summaries(self, text):
        if not text:
            return
        self.summary_buffer += text
        summaries, self.summary_buffer = _extract_completed_summaries(
            self.summary_buffer
        )
        await self._emit_summary_list(summaries)

    async def emit_summaries_from_full_text(self, text):
        if not text:
            return
        summaries, _ = _extract_completed_summaries(text)
        self.summary_buffer = ""
        await self._emit_summary_list(summaries)

    def _current_preview_segment(self):
        html_body = render_for_telegram_html(self.raw_text)
        if not html_body:
            return ""
        segments = split_html_text(html_body, TELEGRAM_HTML_LIMIT)
        return segments[-1] if segments else ""

    def _should_stream_preview_update(self, preview_segment):
        if not preview_segment or preview_segment == self.active_preview_segment:
            return False
        if self.last_stream_update_at <= 0:
            return True
        elapsed = self._now() - self.last_stream_update_at
        raw_delta = len(self.raw_text) - self.last_stream_raw_len
        return (
            elapsed >= _STREAM_UPDATE_INTERVAL_SECONDS
            or raw_delta >= _STREAM_MIN_UPDATE_CHARS
        )

    def _mark_stream_preview_update(self, preview_segment):
        self.active_preview_segment = preview_segment
        self.last_stream_update_at = self._now()
        self.last_stream_raw_len = len(self.raw_text)

    async def _upsert_live_html(self, html_text, wait_retry=True):
        if self.live_msg is None:
            handler = self._reply_html_once
            args = (html_text,)
        else:
            handler = self._edit_html_once
            args = (self.live_msg, html_text)

        if wait_retry:
            self.live_msg = await self._retry_call(handler, *args)
        else:
            self.live_msg = await handler(*args)
        return self.live_msg

    def _resolved_output_files(self, explicit_files=None):
        if explicit_files is not None:
            return explicit_files
        return _files_from_text(self.raw_text)

    def _render_output_segments(self, files):
        html_body = render_for_telegram_html(self.raw_text)
        if not html_body and files:
            html_body = escape_html(_chii("file"))
        elif not html_body:
            html_body = escape_html(_chii("empty"))

        segments = split_html_text(html_body, TELEGRAM_HTML_LIMIT)
        return segments or [escape_html(_chii("empty"))]

    async def _maybe_stream_preview(self):
        if self._is_retrying():
            return
        preview_segment = self._current_preview_segment()
        if not self._should_stream_preview_update(preview_segment):
            return
        try:
            await self._upsert_live_html(preview_segment, wait_retry=False)
        except RetryAfter:
            return
        self._mark_stream_preview_update(preview_segment)

    async def prime(self):
        placeholder = escape_html(_chii("thinking"))
        await self._upsert_live_html(placeholder)
        self.active_preview_segment = placeholder

    async def add_chunk(self, chunk):
        if chunk:
            self.raw_text += chunk
            await self._maybe_stream_preview()

    async def finalize(self, full_text=None, send_files=True, explicit_files=None):
        if full_text is not None:
            self.raw_text = full_text

        files = self._resolved_output_files(explicit_files)
        segments = self._render_output_segments(files)

        first = segments[0]
        await self._upsert_live_html(first)
        self.active_preview_segment = first
        self.last_stream_update_at = self._now()
        self.last_stream_raw_len = len(self.raw_text)

        for segment in segments[1:]:
            await self._retry_call(self._reply_html_once, segment)

        if send_files:
            await _send_files(self.root_msg, files)

    async def finish_with_notice(self, notice):
        html_notice = escape_html(notice or _chii("stop"))
        if self.live_msg is None:
            await self._retry_call(self._reply_html_once, html_notice)
            return
        await self._retry_call(self._edit_html_once, self.live_msg, html_notice)
        self.active_preview_segment = html_notice


async def _dispatch_pending_ask_user_events(msg):
    while True:
        event = _drain_latest_ask_user_event()
        if event is None:
            break
        await _send_ask_user_menu(msg, event)


class _TelegramTurnStreamCoordinator:
    def __init__(self, root_msg):
        self.root_msg = root_msg
        self.session = None
        self.pending_line = ""
        self.code_fence_len = 0
        self.last_turn = 0

    async def prime(self):
        await self._ensure_session()

    async def add_chunk(self, chunk):
        if not chunk:
            return
        text = self.pending_line + chunk
        self.pending_line = ""
        for line in text.splitlines(keepends=True):
            if _line_complete(line):
                await self._process_line(line)
            elif _maybe_partial_turn_marker(line) or _maybe_partial_code_fence(line):
                self.pending_line = line
            else:
                await self._process_line(line)

    async def finalize(self, done_text="", send_files=True, explicit_files=None):
        await self._flush_pending_line()
        current_done_text = self._completed_session_text(done_text)
        files = self._resolved_done_files(done_text, current_done_text, explicit_files)

        if self.session is None:
            if not current_done_text:
                if send_files and files:
                    await _send_files(self.root_msg, files)
                return
            await self._ensure_session()
            await self._finalize_session(
                current_done_text, send_files=send_files, explicit_files=files
            )
            return

        if not self.session.raw_text.strip() and current_done_text:
            await self._finalize_session(
                current_done_text, send_files=send_files, explicit_files=files
            )
            return

        await self._finalize_session(
            current_done_text or None,
            send_files=False,
            explicit_files=files,
            summary_text=current_done_text or self.session.raw_text,
        )
        if send_files:
            await _send_files(self.root_msg, files)

    async def finish_with_notice(self, notice):
        await self._flush_pending_line()
        await self._ensure_session()
        await self.session.finish_with_notice(notice)

    async def _ensure_session(self):
        if self.session is None:
            self.session = _TelegramReplySession(self.root_msg)
            await self.session.prime()

    def _resolved_done_files(self, done_text, current_done_text, explicit_files=None):
        if explicit_files is not None:
            return explicit_files
        return _files_from_text(done_text or current_done_text)

    async def _emit_full_text_summaries(self, text):
        if not (_ENABLE_TG_SUMMARIES and text and self.session is not None):
            return
        await self.session.emit_summaries_from_full_text(text)

    async def _finalize_session(
        self,
        full_text=None,
        send_files=False,
        explicit_files=None,
        summary_text=None,
    ):
        await self._emit_full_text_summaries(
            summary_text if summary_text is not None else full_text
        )
        await self.session.finalize(
            full_text,
            send_files=send_files,
            explicit_files=explicit_files,
        )

    async def _start_turn(self, marker):
        if self.session is not None and self.session.raw_text.strip():
            await self._finalize_session(
                send_files=False,
                summary_text=self.session.raw_text,
            )
            self.session = None
        await self._ensure_session()
        await self.session.add_chunk(marker)

    async def _add_to_current(self, text):
        if not text:
            return
        await self._ensure_session()
        if _ENABLE_TG_SUMMARIES:
            await self.session.emit_summaries(text)
        await self.session.add_chunk(text)

    async def _process_line(self, line):
        turn_no = _turn_marker_number(line)
        if self.code_fence_len == 0 and turn_no == self.last_turn + 1:
            self.last_turn = turn_no
            await self._start_turn(line)
            return
        await self._add_to_current(line)
        match = _CODE_FENCE_RE.match(line or "")
        if match:
            fence_len = len(match.group(1))
            if self.code_fence_len:
                if fence_len >= self.code_fence_len:
                    self.code_fence_len = 0
            else:
                self.code_fence_len = fence_len

    async def _flush_pending_line(self):
        if not self.pending_line:
            return
        line = self.pending_line
        self.pending_line = ""
        await self._add_to_current(line)

    def _completed_session_text(self, done_text):
        done = done_text or ""
        if not done:
            return self.session.raw_text if self.session is not None else ""
        if self.last_turn > 0:
            marker = f"LLM Running (Turn {self.last_turn}) ..."
            pos = done.rfind(marker)
            if pos != -1:
                return done[pos:]
        current = self.session.raw_text if self.session is not None else ""
        if current:
            pos = done.rfind(current)
            if pos != -1:
                return done[pos:]
        return done


async def _stream(dq, msg):
    stream = _TelegramTurnStreamCoordinator(msg)
    await stream.prime()
    try:
        while True:
            try:
                first = await asyncio.to_thread(dq.get, True, _QUEUE_WAIT_SECONDS)
            except Q.Empty:
                continue

            items = [first]
            try:
                while True:
                    items.append(dq.get_nowait())
            except Q.Empty:
                pass

            done_item = None
            for item in items:
                chunk = item.get("next", "")
                if chunk:
                    await stream.add_chunk(chunk)
                await _dispatch_pending_ask_user_events(msg)
                if "done" in item:
                    done_item = item
                    break

            if done_item is not None:
                explicit_files = _files_from_done_item(done_item)
                await stream.finalize(
                    done_item.get("done", ""), explicit_files=explicit_files
                )
                await _dispatch_pending_ask_user_events(msg)
                break
    except asyncio.CancelledError:
        await stream.finish_with_notice(_chii("stop"))
    except RetryAfter as exc:
        print(f"[TG stream retry_after] {type(exc).__name__}: {exc}", flush=True)
    except Exception as exc:
        print(f"[TG stream error] {type(exc).__name__}: {exc}", flush=True)
        await stream.finish_with_notice(_chii("error"))


def _normalized_command(text):
    parts = (text or "").strip().split(None, 1)
    if not parts:
        return ""
    head = parts[0].lower()
    if head.startswith("/"):
        head = "/" + head[1:].split("@", 1)[0]
    return head + (
        f" {parts[1].strip()}" if len(parts) > 1 and parts[1].strip() else ""
    )


async def _cancel_stream_task(ctx):
    task = ctx.user_data.pop("stream_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            print(f"[TG stream cancel] {type(exc).__name__}: {exc}", flush=True)


async def _sync_commands(application):
    await application.bot.set_my_commands(
        [
            BotCommand(command, description)
            for command, description in TELEGRAM_MENU_COMMANDS
        ]
    )


async def _reply_html(message, text):
    html_text = render_for_telegram_html(text)
    if not html_text:
        html_text = escape_html(text or "")
    segments = split_html_text(html_text, TELEGRAM_HTML_LIMIT)
    last_msg = None
    for segment in segments or [escape_html("...")]:
        last_msg = await message.reply_text(segment, parse_mode=ParseMode.HTML)
    return last_msg


async def _reply_command_text(message, text):
    for segment in _markdown_safe_segments(text) or ["..."]:
        try:
            await message.reply_text(_to_markdown_v2(segment), parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as exc:
            print(f"[TG command markdown fallback] {type(exc).__name__}: {exc}", flush=True)
            await message.reply_text(segment)

async def handle_msg(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    await _cancel_stream_task(ctx)
    _apply_tg_extra_system_prompt()
    prompt = _build_text_prompt(update.message.text)
    dq = agent.put_task(prompt, source="telegram")
    task = asyncio.create_task(_stream(dq, update.message))
    ctx.user_data["stream_task"] = task


async def handle_ask_callback(update, ctx):
    query = update.callback_query
    if query is None:
        return
    uid = update.effective_user.id if update.effective_user else None
    if ALLOWED and uid not in ALLOWED:
        return await query.answer("no", show_alert=True)

    menu_id, action = _parse_ask_callback_data(query.data)
    if not menu_id:
        return await query.answer("菜单无效")

    event = _normalize_ask_menu_event(_ask_menu_store.get(menu_id))
    if event is None:
        await query.answer("菜单已过期")
        return await _clear_ask_reply_markup(query)

    candidates = event["candidates"]
    if action == _ASK_CANCEL_ACTION:
        _ask_menu_store.pop(menu_id, None)
        await query.answer()
        await _edit_ask_user_result(query, event, cancelled=True)
        if query.message is not None:
            await _reply_html(query.message, _ASK_CANCEL_PROMPT)
        return

    try:
        selected = candidates[int(action)]
    except (ValueError, IndexError):
        return await query.answer("菜单无效")

    _ask_menu_store.pop(menu_id, None)
    await query.answer()
    await _edit_ask_user_result(query, event, selected=selected)
    if query.message is None:
        return

    await _cancel_stream_task(ctx)
    _apply_tg_extra_system_prompt()
    plan_metadata = active_plan_metadata(agent, _plan_scope_id(update))
    if plan_metadata:
        dq = agent.put_task(
            build_plan_followup_prompt(selected),
            source="telegram_plan",
            metadata=plan_metadata,
        )
    else:
        dq = agent.put_task(_build_text_prompt(selected), source="telegram")
    task = asyncio.create_task(_stream(dq, query.message))
    ctx.user_data["stream_task"] = task


async def cmd_abort(update, ctx):
    await _cancel_stream_task(ctx)
    agent.abort()
    await _reply_html(update.message, _chii("stopping"))


async def cmd_llm(update, ctx):
    args = (update.message.text or "").split()
    if len(args) > 1:
        try:
            n = int(args[1])
            agent.next_llm(n)
            _apply_tg_extra_system_prompt()
            await _reply_html(
                update.message, f"✅ 已切换到 [{agent.llm_no}] {agent.get_llm_name()}"
            )
        except (ValueError, IndexError):
            await _reply_html(
                update.message, f"用法: /llm <0-{len(agent.list_llms()) - 1}>"
            )
    else:
        lines = [
            f"{'→' if cur else '  '} [{i}] {name}" for i, name, cur in agent.list_llms()
        ]
        await _reply_html(update.message, "LLMs:\n" + "\n".join(lines))


async def handle_photo(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    await _cancel_stream_task(ctx)

    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        fpath = f"tg_{photo.file_unique_id}.jpg"
        kind = "图片"
    elif update.message.document:
        doc = update.message.document
        file = await doc.get_file()
        ext = os.path.splitext(doc.file_name or "")[1] or ""
        fpath = f"tg_{doc.file_unique_id}{ext}"
        kind = "文件"
    else:
        return

    await file.download_to_drive(os.path.join(_TEMP_DIR, fpath))
    caption = update.message.caption
    if caption:
        prompt = f"[TIPS] 收到{kind}temp/{fpath}\n{caption}"
    else:
        prompt = f"[TIPS] 收到{kind}temp/{fpath}，请等待下一步指令"

    _apply_tg_extra_system_prompt()
    dq = agent.put_task(prompt, source="telegram")
    task = asyncio.create_task(_stream(dq, update.message))
    ctx.user_data["stream_task"] = task


async def handle_command(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")

    cmd = _normalized_command(update.message.text)
    op = cmd.split()[0] if cmd else ""

    if op == "/help":
        return await _reply_html(update.message, HELP_TEXT)
    if op == "/status":
        llm = agent.get_llm_name() if agent.llmclient else "未配置"
        status_line = (
            _chii("status_running") if agent.is_running else _chii("status_idle")
        )
        return await _reply_html(
            update.message, f"状态: {status_line}\nLLM: [{agent.llm_no}] {llm}"
        )
    if op == "/stop":
        return await cmd_abort(update, ctx)
    if op == "/llm":
        return await cmd_llm(update, ctx)
    if op == "/btw":
        answer = await asyncio.to_thread(handle_btw_frontend_command, agent, cmd)
        return await _reply_command_text(update.message, answer)
    if op == "/new":
        await _cancel_stream_task(ctx)
        return await _reply_html(update.message, reset_conversation(agent))
    if op == "/restore":
        await _cancel_stream_task(ctx)
        try:
            restored_info, err = format_restore()
            if err:
                return await _reply_html(update.message, err)
            restored, fname, count = restored_info
            agent.abort()
            agent.history.extend(restored)
            return await _reply_html(
                update.message,
                f"✅ 已恢复 {count} 轮对话\n来源: {fname}\n(仅恢复上下文，请输入新问题继续)",
            )
        except Exception as e:
            return await _reply_html(update.message, f"❌ 恢复失败: {e}")
    if op == "/continue":
        if cmd != "/continue":
            await _cancel_stream_task(ctx)
        return await _reply_html(update.message, handle_frontend_command(agent, cmd))

    if op == "/plan":
        await _cancel_stream_task(ctx)
        result = handle_plan_frontend(agent, cmd, scope_id=_plan_scope_id(update))
        if getattr(result, "kind", "") != "start_plan":
            return await _reply_html(update.message, result.reply_text)
        _apply_tg_extra_system_prompt()
        dq = agent.put_task(
            result.prompt,
            source="telegram_plan",
            metadata=result.metadata,
        )
        task = asyncio.create_task(_stream(dq, update.message))
        ctx.user_data["stream_task"] = task
        return

    return await _reply_html(update.message, HELP_TEXT)


if __name__ == "__main__":
    _LOCK_SOCK = ensure_single_instance(19527, "Telegram")
    if not ALLOWED:
        print(
            "[Telegram] ERROR: tg_allowed_users in mykey.py is empty or missing. Set it to avoid unauthorized access."
        )
        sys.exit(1)

    require_runtime(agent, "Telegram", tg_bot_token=mykeys.get("tg_bot_token"))
    redirect_log(__file__, "tgapp.log", "Telegram", ALLOWED)
    _apply_tg_extra_system_prompt()
    _register_ask_user_hook()
    threading.Thread(target=agent.run, daemon=True).start()

    proxy = mykeys.get("proxy")
    print("proxy:", proxy if proxy else "<disabled>")
    _NOTIFY_CHAT_ID = os.environ.get("GA_NOTIFY_CHAT_ID", "")
    _SHUTDOWN_FILE = os.environ.get("GA_SHUTDOWN_FILE", "")
    _RUNTIME_FLAGS = {"startup_notified": False, "shutdown_done": False}

    async def _error_handler(update, context: ContextTypes.DEFAULT_TYPE):
        print(f"[{time.strftime('%m-%d %H:%M')}] TG error: {context.error}", flush=True)

    async def _post_init(app):
        await _sync_commands(app)

        if _NOTIFY_CHAT_ID and not _RUNTIME_FLAGS["startup_notified"]:
            try:
                await _send_notify_event(app.bot, _NOTIFY_CHAT_ID, "wake")
                _RUNTIME_FLAGS["startup_notified"] = True
                print(
                    f"[{time.strftime('%m-%d %H:%M')}] TG startup notify sent to {_NOTIFY_CHAT_ID}",
                    flush=True,
                )
            except Exception as exc:
                print(
                    f"[{time.strftime('%m-%d %H:%M')}] TG startup notify failed: {exc}",
                    flush=True,
                )

        if not _SHUTDOWN_FILE or app.bot_data.get("_shutdown_watch_task") is not None:
            return

        async def _watch_shutdown():
            try:
                while not _RUNTIME_FLAGS["shutdown_done"]:
                    if os.path.exists(_SHUTDOWN_FILE):
                        _RUNTIME_FLAGS["shutdown_done"] = True
                        if _NOTIFY_CHAT_ID:
                            try:
                                await _send_notify_event(
                                    app.bot, _NOTIFY_CHAT_ID, "sleep"
                                )
                                print(
                                    f"[{time.strftime('%m-%d %H:%M')}] TG shutdown notify sent",
                                    flush=True,
                                )
                            except Exception as exc:
                                print(
                                    f"[{time.strftime('%m-%d %H:%M')}] TG shutdown notify failed: {exc}",
                                    flush=True,
                                )
                        try:
                            os.remove(_SHUTDOWN_FILE)
                        except Exception:
                            pass
                        await app.stop()
                        return
                    await asyncio.sleep(3)
            except asyncio.CancelledError:
                return

        app.bot_data["_shutdown_watch_task"] = asyncio.create_task(_watch_shutdown())

    while True:
        try:
            print(f"TG bot starting... {time.strftime('%m-%d %H:%M')}")
            request_kwargs = dict(
                read_timeout=30, write_timeout=30, connect_timeout=30, pool_timeout=30
            )
            if proxy:
                request_kwargs["proxy"] = proxy
            request = HTTPXRequest(**request_kwargs)
            app = (
                ApplicationBuilder()
                .token(mykeys["tg_bot_token"])
                .request(request)
                .get_updates_request(request)
                .post_init(_post_init)
                .build()
            )
            app.add_handler(CallbackQueryHandler(handle_ask_callback, pattern=r"^ask:"))
            app.add_handler(MessageHandler(filters.COMMAND, handle_command))
            app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
            app.add_handler(MessageHandler(filters.Document.ALL, handle_photo))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
            app.add_error_handler(_error_handler)
            app.run_polling(drop_pending_updates=True, poll_interval=1.0, timeout=30)
            if _RUNTIME_FLAGS["shutdown_done"]:
                print(
                    f"[{time.strftime('%m-%d %H:%M')}] TG bot shut down gracefully",
                    flush=True,
                )
                break
        except Exception as e:
            if _RUNTIME_FLAGS["shutdown_done"]:
                break
            print(f"[{time.strftime('%m-%d %H:%M')}] polling crashed: {e}", flush=True)
            time.sleep(10)
            asyncio.set_event_loop(asyncio.new_event_loop())
