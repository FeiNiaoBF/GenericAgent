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


def _chii(key):
    return get_phrase(key, pool=_CHII)


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
        self.retry_until = 0.0
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

    async def _reply_html_once(self, html_text):
        try:
            return await self.root_msg.reply_text(html_text, parse_mode=ParseMode.HTML)
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception:
            fallback_text = render_for_telegram_plain_text(self.raw_text) or "..."
            return await self.root_msg.reply_text(fallback_text)

    async def _edit_html_once(self, msg, html_text):
        try:
            updated = await msg.edit_text(html_text, parse_mode=ParseMode.HTML)
        except RetryAfter as exc:
            self._set_retry_after(exc)
            raise
        except Exception as exc:
            if _is_not_modified_error(exc):
                return msg
            fallback_text = render_for_telegram_plain_text(self.raw_text) or "..."
            updated = await msg.edit_text(fallback_text)
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
                safe_summary = summary.replace("<_quote_>", "").replace(
                    "</_quote_>", ""
                )
                html_summary = render_for_telegram_html(
                    f"<_quote_>{safe_summary}</_quote_>"
                )
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
            safe_summary = summary.replace("<_quote_>", "").replace("</_quote_>", "")
            safe_summary = safe_summary.replace("<blockquote>", "").replace(
                "</blockquote>", ""
            )
            html_summary = render_for_telegram_html(
                f"<_quote_>{safe_summary}</_quote_>"
            )
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

    async def prime(self):
        placeholder = escape_html(_chii("thinking"))
        self.live_msg = await self._retry_call(self._reply_html_once, placeholder)

    async def add_chunk(self, chunk):
        if chunk:
            self.raw_text += chunk

    async def finalize(self, full_text=None, send_files=True, explicit_files=None):
        if full_text is not None:
            self.raw_text = full_text

        files = (
            explicit_files
            if explicit_files is not None
            else _files_from_text(self.raw_text)
        )
        html_body = render_for_telegram_html(self.raw_text)
        if not html_body and files:
            html_body = escape_html(_chii("file"))
        elif not html_body:
            html_body = escape_html(_chii("empty"))

        segments = split_html_text(html_body, TELEGRAM_HTML_LIMIT)
        if not segments:
            segments = [escape_html(_chii("empty"))]

        first = segments[0]
        if self.live_msg is None:
            self.live_msg = await self._retry_call(self._reply_html_once, first)
        else:
            self.live_msg = await self._retry_call(
                self._edit_html_once, self.live_msg, first
            )

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


async def _dispatch_pending_ask_user_events(msg):
    while True:
        event = _drain_latest_ask_user_event()
        if event is None:
            break
        await _send_ask_user_menu(msg, event)


async def _stream(dq, msg):
    session = _TelegramReplySession(msg)
    await session.prime()
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
                    await session.emit_summaries(chunk)
                    await session.add_chunk(chunk)
                await _dispatch_pending_ask_user_events(msg)
                if "done" in item:
                    done_item = item
                    break

            if done_item is not None:
                await session.emit_summaries_from_full_text(done_item.get("done", ""))
                explicit_files = _files_from_done_item(done_item)
                await session.finalize(
                    done_item.get("done", ""), explicit_files=explicit_files
                )
                await _dispatch_pending_ask_user_events(msg)
                break
    except asyncio.CancelledError:
        await session.finish_with_notice(_chii("stop"))
    except RetryAfter as exc:
        print(f"[TG stream retry_after] {type(exc).__name__}: {exc}", flush=True)
    except Exception as exc:
        print(f"[TG stream error] {type(exc).__name__}: {exc}", flush=True)
        await session.finish_with_notice(_chii("error"))


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


async def handle_msg(update, ctx):
    uid = update.effective_user.id
    if ALLOWED and uid not in ALLOWED:
        return await update.message.reply_text("no")
    await _cancel_stream_task(ctx)
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
