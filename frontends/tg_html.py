import html
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse

from chatapp_common import clean_reply

TELEGRAM_HTML_LIMIT = 4000

_CODE_TOKEN_RE = re.compile(r"(`{3,})([A-Za-z0-9_+-]*)\n([\s\S]*?)\1", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_BOLD_RE = re.compile(r"\*\*([^\n]+?)\*\*|__([^\n]+?)__")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)([^\n]+?)(?<!\*)\*(?!\*)|(?<!_)_([^\n]+?)(?<!_)_")
_STRIKE_RE = re.compile(r"~~([^\n]+?)~~")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
_TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
_TABLE_CELL_MAX_WIDTH = 40
_TURN_MARKER_RE = re.compile(r"^\*{0,2}LLM Running \(Turn \d+\) \.\.\.\*{0,2}\s*$", re.MULTILINE)
_INTERNAL_QUOTE_RE = re.compile(r"<_quote_>([\s\S]*?)</_quote_>", re.DOTALL)
_FILE_MARKER_RE = re.compile(r"\[FILE:([^\]]+)\]")
_SUMMARY_CAPTURE_RE = re.compile(r"<summary>\s*(.*?)\s*</summary>", re.IGNORECASE | re.DOTALL)
_SUMMARY_BLOCK_RE = re.compile(r"<summary>\s*[\s\S]*?\s*</summary>", re.IGNORECASE)
_SUMMARY_OPEN_TAG = "<summary>"
_SUMMARY_CLOSE_TAG = "</summary>"
_SUMMARY_MAX_CHARS = 120
_ALLOWED_TAGS = {
    "b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
    "code", "pre", "a", "blockquote",
}
_ALLOWED_TAG_PATTERN = "|".join(sorted(_ALLOWED_TAGS, key=len, reverse=True))
_ALLOWED_HTML_TAG_RE = re.compile(
    rf"<\s*/?\s*(?:{_ALLOWED_TAG_PATTERN})(?:\s+[^<>]*?)?\s*>",
    re.IGNORECASE,
)


def escape_html(text):
    return html.escape(text or "", quote=False)


def tg_html_escape(text):
    return escape_html(text)


def _strip_turn_markers(text):
    return _TURN_MARKER_RE.sub("", text or "")


def _render_file_markers(text):
    return _FILE_MARKER_RE.sub(lambda m: os.path.basename(m.group(1)), text or "")


def _normalize_summary_text(text):
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if len(normalized) <= _SUMMARY_MAX_CHARS:
        return normalized
    return normalized[: _SUMMARY_MAX_CHARS - 3].rstrip() + "..."


def _split_summary_content(text):
    candidate = (text or "").strip()
    if not candidate:
        return "", ""

    parts = re.split(r"\n\s*\n", candidate, maxsplit=1)
    if len(parts) == 2:
        summary_part, spill = parts[0], parts[1]
    else:
        lines = [line.strip() for line in candidate.splitlines() if line.strip()]
        if not lines:
            return "", ""
        summary_part = lines[0]
        spill = "\n".join(lines[1:]).strip()

    summary = _normalize_summary_text(summary_part)
    return summary, spill.strip()


def _extract_summary_sections(text):
    raw = text or ""
    summaries = []
    spilled_bodies = []

    def _repl(match):
        summary, spill = _split_summary_content(match.group(1))
        if summary:
            summaries.append(summary)
        if spill:
            spilled_bodies.append(spill)
        return ""

    remainder = _SUMMARY_CAPTURE_RE.sub(_repl, raw)

    first_open = remainder.find(_SUMMARY_OPEN_TAG)
    first_close = remainder.find(_SUMMARY_CLOSE_TAG)
    if first_close != -1 and (first_open == -1 or first_close < first_open):
        prefix = remainder[:first_close].strip()
        summary, spill = _split_summary_content(prefix)
        if summary:
            summaries.append(summary)
        if spill:
            spilled_bodies.append(spill)
        remainder = remainder[first_close + len(_SUMMARY_CLOSE_TAG) :]

    open_pos = remainder.find(_SUMMARY_OPEN_TAG)
    close_pos = remainder.find(_SUMMARY_CLOSE_TAG)
    if open_pos != -1 and (close_pos == -1 or open_pos > close_pos):
        suffix = remainder[open_pos + len(_SUMMARY_OPEN_TAG) :].strip()
        summary, spill = _split_summary_content(suffix)
        if summary:
            summaries.append(summary)
        if spill:
            spilled_bodies.append(spill)
        remainder = remainder[:open_pos]

    if spilled_bodies:
        remainder = "\n\n".join(part for part in spilled_bodies + [remainder] if part.strip())

    return summaries, remainder


def _strip_summary_artifacts(text):
    cleaned = _SUMMARY_BLOCK_RE.sub("", text or "")

    while True:
        open_pos = cleaned.find(_SUMMARY_OPEN_TAG)
        close_pos = cleaned.find(_SUMMARY_CLOSE_TAG)
        if close_pos == -1 or (open_pos != -1 and open_pos < close_pos):
            break
        cleaned = cleaned[close_pos + len(_SUMMARY_CLOSE_TAG) :]

    open_pos = cleaned.rfind(_SUMMARY_OPEN_TAG)
    close_pos = cleaned.rfind(_SUMMARY_CLOSE_TAG)
    if open_pos != -1 and open_pos > close_pos:
        cleaned = cleaned[:open_pos]

    return cleaned.replace(_SUMMARY_OPEN_TAG, "").replace(_SUMMARY_CLOSE_TAG, "")


def _render_summary_block(summary):
    content = (summary or "").strip()
    if not content:
        return ""

    inline_codes = []

    def _code_repl(match):
        token = f"@@TGSUMCODE{len(inline_codes)}@@"
        inline_codes.append((token, escape_html(match.group(1) or "")))
        return token

    tokenized = _INLINE_CODE_RE.sub(_code_repl, _render_file_markers(content))
    formatted = _apply_markdown_to_html(escape_html(tokenized))
    for token, safe_code in inline_codes:
        formatted = formatted.replace(token, f"<code>{safe_code}</code>")
    formatted = _TelegramHTMLSanitizer().sanitize(formatted).strip()
    return f"<blockquote><b>摘要</b>\n{formatted}</blockquote>"


def _extract_code_blocks(text):
    blocks = []

    def _repl(match):
        lang = re.sub(r"[^A-Za-z0-9_+-]", "", match.group(2) or "")
        code = match.group(3) or ""
        token = f"@@TGCODE{len(blocks)}@@"
        blocks.append((token, lang, code))
        return token

    return _CODE_TOKEN_RE.sub(_repl, text or ""), blocks


def _parse_table_row(line):
    stripped = (line or "").strip()
    if "|" not in stripped:
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip() for cell in stripped.split("|")]
    if len(cells) < 2:
        return None
    return cells


def _is_table_separator(line, expected_cols):
    cells = _parse_table_row(line)
    if not cells or len(cells) != expected_cols:
        return False
    return all(_TABLE_SEPARATOR_CELL_RE.fullmatch(cell or "") for cell in cells)


def _truncate_table_cell(cell, max_width=_TABLE_CELL_MAX_WIDTH):
    text = cell or ""
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3].rstrip() + "..."


def _render_table_block(header, rows):
    header = [_truncate_table_cell(cell) for cell in header]
    rows = [[_truncate_table_cell(cell) for cell in row] for row in rows]
    all_rows = [header] + rows
    col_count = len(header)
    widths = [0] * col_count
    for row in all_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _format_row(cells):
        padded = [cells[i].ljust(widths[i]) for i in range(col_count)]
        return "| " + " | ".join(padded) + " |"

    separator = "|-" + "-|-".join("-" * widths[i] for i in range(col_count)) + "-|"
    lines = [_format_row(header), separator]
    lines.extend(_format_row(row) for row in rows)
    return "\n".join(lines)


def _extract_markdown_tables(text):
    lines = (text or "").splitlines()
    out = []
    blocks = []
    i = 0
    while i < len(lines):
        header = _parse_table_row(lines[i])
        if not header or i + 1 >= len(lines) or not _is_table_separator(lines[i + 1], len(header)):
            out.append(lines[i])
            i += 1
            continue

        j = i + 2
        rows = []
        while j < len(lines):
            parsed = _parse_table_row(lines[j])
            if not parsed or len(parsed) != len(header):
                break
            rows.append(parsed)
            j += 1

        token = f"@@TGTABLE{len(blocks)}@@"
        blocks.append((token, _render_table_block(header, rows)))
        out.append(token)
        i = j

    return "\n".join(out), blocks


def _format_headings(text):
    lines = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if not m:
            lines.append(line)
            continue
        header = m.group(2).strip()
        if not header:
            lines.append(line)
            continue
        lines.append(f"<b>{header}</b>")
    return "\n".join(lines)


def _format_blockquotes(text):
    out = []
    quote_buf = []
    for line in (text or "").splitlines():
        if line.lstrip().startswith("&gt;"):
            quote_line = line.lstrip()[4:].lstrip()
            quote_buf.append(quote_line)
            continue
        if quote_buf:
            quote_text = "\n".join(quote_buf)
            out.append(f"<blockquote>{quote_text}</blockquote>")
            quote_buf = []
        out.append(line)
    if quote_buf:
        quote_text = "\n".join(quote_buf)
        out.append(f"<blockquote>{quote_text}</blockquote>")
    return "\n".join(out)


def _apply_markdown_to_html(escaped_text):
    text = _format_headings(escaped_text)
    text = _format_blockquotes(text)
    text = _INLINE_CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", text)
    text = _BOLD_RE.sub(lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    text = _ITALIC_RE.sub(lambda m: f"<i>{m.group(1) or m.group(2)}</i>", text)
    text = _STRIKE_RE.sub(lambda m: f"<s>{m.group(1)}</s>", text)

    def _link_repl(match):
        label = match.group(1)
        url = match.group(2)
        safe_url = html.escape(url, quote=True)
        return f"<a href=\"{safe_url}\">{label}</a>"

    text = _LINK_RE.sub(_link_repl, text)
    return text


def _reinsert_code_blocks(text, blocks):
    out = text
    for token, lang, code in blocks:
        safe_code = escape_html(code)
        if lang:
            out = out.replace(token, f"<pre><code class=\"language-{lang}\">{safe_code}</code></pre>")
        else:
            out = out.replace(token, f"<pre><code>{safe_code}</code></pre>")
    return out


def _reinsert_table_blocks(text, blocks):
    out = text
    for token, table_text in blocks:
        safe_table = escape_html(table_text)
        out = out.replace(token, f"<pre><code>{safe_table}</code></pre>")
    return out


def _extract_allowed_html_tags(text):
    tags = []

    def _repl(match):
        token = f"@@TGHTMLTAG{len(tags)}@@"
        tags.append((token, match.group(0)))
        return token

    return _ALLOWED_HTML_TAG_RE.sub(_repl, text or ""), tags


def _reinsert_allowed_html_tags(text, tags):
    out = text
    for token, markup in tags:
        out = out.replace(token, markup)
    return out


def _normalize_internal_quotes(text):
    def _quote_repl(match):
        content = (match.group(1) or "").strip()
        if not content:
            return ""
        escaped = escape_html(content)
        return f"<blockquote>{escaped}</blockquote>"

    return _INTERNAL_QUOTE_RE.sub(_quote_repl, text or "")


def _is_safe_href(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        return True
    return parsed.scheme in {"http", "https", "mailto", "tg"}


class _TelegramHTMLSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in _ALLOWED_TAGS:
            return
        safe_attrs = []
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value and _is_safe_href(value):
                    safe_attrs.append(("href", value))
        elif tag == "code":
            for key, value in attrs:
                if key == "class" and value and re.fullmatch(r"language-[A-Za-z0-9_+-]+", value):
                    safe_attrs.append(("class", value))
        elif tag == "blockquote":
            for key, value in attrs:
                if key == "expandable":
                    safe_attrs.append(("expandable", value))
        if safe_attrs:
            rendered = " ".join(
                f"{name}=\"{html.escape(str(value or ''), quote=True)}\"" if value is not None else name
                for name, value in safe_attrs
            )
            self.parts.append(f"<{tag} {rendered}>")
            return
        self.parts.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in _ALLOWED_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(html.escape(data or "", quote=False))

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def sanitize(self, markup):
        self.parts = []
        self.feed(markup or "")
        self.close()
        return "".join(self.parts)


class _TelegramPlainTextRenderer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def _append_newline(self):
        if not self.parts:
            return
        if self.parts[-1].endswith("\n"):
            return
        self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            self.parts.append("\n")
        elif tag in {"blockquote", "pre"}:
            self._append_newline()

    def handle_endtag(self, tag):
        if tag in {"blockquote", "pre"}:
            self._append_newline()

    def handle_data(self, data):
        if data:
            self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name):
        self.parts.append(html.unescape(f"&#{name};"))

    def render(self, markup):
        self.parts = []
        self.feed(markup or "")
        self.close()
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def render_for_telegram_html(raw_text):
    summary_source = _render_file_markers(_strip_turn_markers(raw_text or ""))
    summaries, remainder = _extract_summary_sections(summary_source)
    cleaned = clean_reply(remainder) if (remainder or "").strip() else ""
    cleaned = _strip_summary_artifacts(cleaned)
    cleaned = _strip_turn_markers(cleaned)
    cleaned = _render_file_markers(cleaned)
    cleaned = _normalize_internal_quotes(cleaned)

    tokenized, blocks = _extract_code_blocks(cleaned)
    tokenized, table_blocks = _extract_markdown_tables(tokenized)
    tokenized, raw_html_tags = _extract_allowed_html_tags(tokenized)
    escaped = escape_html(tokenized)
    with_markup = _apply_markdown_to_html(escaped)
    with_code = _reinsert_code_blocks(with_markup, blocks)
    with_tables = _reinsert_table_blocks(with_code, table_blocks)
    with_raw_html = _reinsert_allowed_html_tags(with_tables, raw_html_tags)
    sanitized = _TelegramHTMLSanitizer().sanitize(with_raw_html)
    summary_markup = _render_summary_block(summaries[-1]) if summaries else ""
    if summary_markup and sanitized.strip():
        return f"{summary_markup}\n\n{sanitized.strip()}"
    if summary_markup:
        return summary_markup
    return sanitized.strip()


def render_for_telegram_plain_text(raw_text):
    html_text = render_for_telegram_html(raw_text)
    if not html_text:
        summary_source = _render_file_markers(_strip_turn_markers(raw_text or ""))
        _, remainder = _extract_summary_sections(summary_source)
        cleaned = clean_reply(remainder) if (remainder or "").strip() else ""
        cleaned = _strip_summary_artifacts(cleaned)
        cleaned = _strip_turn_markers(cleaned)
        cleaned = _render_file_markers(cleaned)
        return cleaned.strip()
    return _TelegramPlainTextRenderer().render(html_text)


def _tokenize_html(html_text):
    tokens = []
    for part in re.split(r"(<[^>]+>)", html_text or ""):
        if part:
            tokens.append(part)
    return tokens


def _tag_name(tag_text):
    m = re.match(r"</?\s*([a-zA-Z0-9]+)", tag_text or "")
    return m.group(1).lower() if m else ""


def _close_stack(stack):
    return "".join(f"</{name}>" for name, _ in reversed(stack))


def _open_stack(stack):
    return "".join(start_tag for _, start_tag in stack)


def split_html_text(html_text, limit=TELEGRAM_HTML_LIMIT):
    text = (html_text or "").strip()
    if not text:
        return []
    if len(text) <= limit:
        return [text]

    tokens = _tokenize_html(text)
    parts = []
    current = ""
    stack = []

    def flush_current():
        nonlocal current
        if not current:
            return
        segment = current + _close_stack(stack)
        parts.append(segment)
        current = _open_stack(stack)

    for token in tokens:
        if token.startswith("<") and token.endswith(">"):
            tag_name = _tag_name(token)
            is_end = token.startswith("</")
            is_self = token.endswith("/>")
            if is_end:
                if stack and stack[-1][0] == tag_name:
                    stack.pop()
            elif not is_self and tag_name in _ALLOWED_TAGS:
                stack.append((tag_name, token))

            if len(current) + len(token) > limit:
                flush_current()
            current += token
            continue

        remaining = token
        while remaining:
            room = limit - len(current)
            if room <= 0:
                flush_current()
                room = limit - len(current)

            if len(remaining) <= room:
                current += remaining
                remaining = ""
                continue

            cut = remaining.rfind("\n", 0, room)
            if cut < max(1, int(room * 0.6)):
                cut = remaining.rfind(" ", 0, room)
            if cut < max(1, int(room * 0.6)):
                cut = room
            current += remaining[:cut]
            remaining = remaining[cut:].lstrip()
            flush_current()

    if current:
        parts.append(current + _close_stack(stack))

    return [p for p in parts if p.strip()] or [text[:limit]]
