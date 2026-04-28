"""
Telegram message formatting module with official recommended format.
Provides HTML-first formatting with Markdown fallback strategy.

Official Telegram Bot API formatting guide:
- HTML: Simple and robust, official recommendation for new bots
- MarkdownV2: More complex escaping, use as fallback only
"""

import html
import re

# Handle imports gracefully for testing
try:
    from telegram.constants import ParseMode
except ImportError:
    # Fallback for testing without telegram library
    class ParseMode:
        HTML = "HTML"
        MARKDOWN_V2 = "MarkdownV2"

# Regex to detect and protect code blocks
_CODE_BLOCK_RE = re.compile(r"```([A-Za-z0-9_+-]*)\r?\n([\s\S]*?)```", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")

# Use special markers that won't be processed as Markdown
_PLACEHOLDER_PREFIX = "\x00"  # null byte, won't be processed
_PLACEHOLDER_SUFFIX = "\x00"
_ALLOWED_HTML_TAG_RE = re.compile(
    r"</?(?:b|strong|i|em|u|s|del|tg-spoiler|blockquote|pre)(?:\s[^>]*)?>"
    r"|<code(?:\s+class=\"[^\"]*\")?>"
    r"|</code>"
    r"|<a\s+href=\"[^\"]+\">"
    r"|</a>",
    re.IGNORECASE,
)
_MDV2_SPECIAL_CHARS = "\\_*[]()~`>#+-=|{}.!"
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_BLOCKQUOTE_LINE_RE = re.compile(r"^>+\s?(.*)")


def _escape_mdv2(s):
    for char in _MDV2_SPECIAL_CHARS:
        s = s.replace(char, "\\" + char)
    return s


def _restore_text_map(text, protected):
    for placeholder, original in protected.items():
        text = text.replace(placeholder, original)
    return text


def _extract_protected_regions(text):
    """
    Extract code blocks and inline code to protect them from formatting.
    Returns: (processed_text, protected_regions_dict)
    where protected_regions_dict maps placeholder to original content.
    """
    if not text:
        return text, {}

    protected = {}
    placeholder_id = 0

    # Extract fenced code blocks first (higher priority)
    def replace_block(match):
        nonlocal placeholder_id
        placeholder = f"{_PLACEHOLDER_PREFIX}CODEBLOCK_{placeholder_id}{_PLACEHOLDER_SUFFIX}"
        lang = match.group(1) or ""
        code = match.group(2) or ""
        protected[placeholder] = ("block", lang, code)
        placeholder_id += 1
        return placeholder

    text = _CODE_BLOCK_RE.sub(replace_block, text)

    # Extract inline code
    def replace_inline(match):
        nonlocal placeholder_id
        placeholder = f"{_PLACEHOLDER_PREFIX}INLINECODE_{placeholder_id}{_PLACEHOLDER_SUFFIX}"
        protected[placeholder] = ("inline", "", match.group(1) or "")
        placeholder_id += 1
        return placeholder

    text = _INLINE_CODE_RE.sub(replace_inline, text)
    return text, protected


def _restore_protected_regions(text, protected):
    """Restore original code blocks and inline code."""
    restored = {}
    for placeholder, (kind, lang, code) in protected.items():
        restored[placeholder] = (
            f"```{lang}\n{code}```" if kind == "block" and lang
            else f"```\n{code}```" if kind == "block"
            else f"`{code}`"
        )
    return _restore_text_map(text, restored)


def _extract_blockquotes(text):
    """Extract markdown blockquote lines (> text) into placeholders.

    Must be called BEFORE html.escape because > becomes &gt; after escaping.
    Consecutive > lines are merged into a single <blockquote> block.
    Stored raw content (with any code/link placeholders already applied)
    so inline formatting can be applied at restore time.
    """
    if not text:
        return text, {}

    protected = {}
    bq_id = 0
    lines = text.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        m = _BLOCKQUOTE_LINE_RE.match(lines[i])
        if m:
            bq_content_lines = []
            while i < len(lines):
                bm = _BLOCKQUOTE_LINE_RE.match(lines[i])
                if bm:
                    bq_content_lines.append(bm.group(1))
                    i += 1
                else:
                    break
            raw_content = "\n".join(bq_content_lines)
            placeholder = f"{_PLACEHOLDER_PREFIX}BLOCKQUOTE_{bq_id}{_PLACEHOLDER_SUFFIX}"
            protected[placeholder] = raw_content
            result_lines.append(placeholder)
            bq_id += 1
        else:
            result_lines.append(lines[i])
            i += 1

    return "\n".join(result_lines), protected


def _render_blockquote_to_html(raw_content):
    """Render raw blockquote content to Telegram HTML <blockquote>.

    Applies html.escape and inline formatting to the stored raw content.
    Code/link placeholders inside are left intact and restored later.
    """
    escaped = html.escape(raw_content, quote=False)
    escaped = re.sub(r"\*\*\*([^\n]+?)\*\*\*", r"<b><i>\1</i></b>", escaped)
    escaped = re.sub(r"\*\*([^\n]+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"__([^\n]+?)__", r"<u>\1</u>", escaped)
    escaped = re.sub(r"~~([^\n]+?)~~", r"<s>\1</s>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\*)([^\n]+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", escaped)
    return f"<blockquote>{escaped}</blockquote>"


def _convert_headers(text):
    """Convert markdown headers to Telegram HTML bold formatting.

    Called AFTER html.escape (# is not affected by html.escape).
    H1 gets a thick left-bar indicator; H2 is plain bold; H3+ gets a bullet.
    """
    def header_repl(m):
        level = len(m.group(1))
        content = m.group(2).strip()
        if level == 1:
            return f"<b>\u2503 {content}</b>"
        elif level == 2:
            return f"<b>{content}</b>"
        else:
            return f"<b>\u2022 {content}</b>"
    return _HEADER_RE.sub(header_repl, text)


def _extract_allowed_html_tags(text):
    """Protect Telegram-supported HTML tags to avoid escaping user-provided HTML."""
    if not text:
        return text, {}

    protected = {}
    tag_id = 0

    def repl(match):
        nonlocal tag_id
        placeholder = f"{_PLACEHOLDER_PREFIX}HTMLTAG_{tag_id}{_PLACEHOLDER_SUFFIX}"
        protected[placeholder] = match.group(0)
        tag_id += 1
        return placeholder

    return _ALLOWED_HTML_TAG_RE.sub(repl, text), protected


def _render_code_region_to_html(original):
    """Render markdown code regions to Telegram HTML code/pre blocks."""
    kind, lang, code = original
    if kind == "block":
        code_text = html.escape(code, quote=False)
        if lang:
            return f'<pre><code class="language-{lang}">{code_text}</code></pre>'
        return f"<pre><code>{code_text}</code></pre>"
    return f"<code>{html.escape(code, quote=False)}</code>"


def _extract_markdown_links(text):
    """
    Extract markdown links [text](url) into placeholders BEFORE html.escape.
    This prevents URL '&' characters from being double-escaped.
    Returns: (processed_text, link_protected_dict)
    """
    if not text:
        return text, {}

    # Match [text](url) — URL cannot contain ')' or '\n'
    link_re = re.compile(r"\[([^\]]+)\]\(([^)\n]+)\)")
    protected = {}
    link_id = 0

    def replace_link(match):
        nonlocal link_id
        placeholder = f"{_PLACEHOLDER_PREFIX}MDLINK_{link_id}{_PLACEHOLDER_SUFFIX}"
        link_text = match.group(1)
        link_url = match.group(2)
        # HTML-escape both text and URL for safe attribute placement
        safe_text = html.escape(link_text, quote=True)
        safe_url = html.escape(link_url, quote=True)
        protected[placeholder] = f'<a href="{safe_url}">{safe_text}</a>'
        link_id += 1
        return placeholder

    text = link_re.sub(replace_link, text)
    return text, protected


def _is_table_separator_line(line):
    """Check if a line is a markdown table separator (|---| format)."""
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return False
    inner = s[1:-1].strip()
    if not inner:
        return False
    parts = [p.strip() for p in inner.split("|")]
    for part in parts:
        if not part:
            continue
        if not re.match(r"^:?-+:?$", part.strip()):
            return False
    return True


def _parse_table_row(row):
    """Parse a markdown table row into cell strings.

    Handles escaped pipes (backslash + pipe) as literal pipe characters within cells.
    Uses a placeholder approach: replace escaped pipe -> placeholder, split by |, restore.
    """
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    # Protect escaped pipes (\|) so they aren't split on
    s = s.replace("\\|", "\x00PIPE\x00")
    cells = s.split("|")
    return [c.strip().replace("\x00PIPE\x00", "|") for c in cells]


def _build_pre_table(rows_text):
    """Build a plain-text ASCII table wrapped in <pre> tags.

    Cell content at this point may contain HTML formatting tags from the
    inline-formatting pass; strip them (and unescape HTML entities) when
    measuring column widths so the monospace layout is correct.
    Telegram does not render HTML <table> tags, so <pre> gives consistent
    monospace display across all clients.
    """
    if len(rows_text) < 2:
        return None

    # Parse rows, skipping the separator row (index 1)
    parsed = []
    for idx, row in enumerate(rows_text):
        if idx == 1:
            continue  # skip |---|---| separator
        parsed.append(_parse_table_row(row))

    if not parsed:
        return None

    num_cols = max(len(r) for r in parsed)
    for row in parsed:
        while len(row) < num_cols:
            row.append("")

    def strip_to_plain(s):
        """Strip HTML tags and unescape entities for width calculation."""
        return html.unescape(re.sub(r"<[^>]+>", "", s))

    plain_rows = [[strip_to_plain(c) for c in row] for row in parsed]
    col_widths = [
        max(len(plain_rows[r][c]) for r in range(len(plain_rows)))
        for c in range(num_cols)
    ]

    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def fmt_row(cells):
        parts = [f" {c:<{col_widths[i]}} " for i, c in enumerate(cells)]
        return "|" + "|".join(parts) + "|"

    lines = [sep, fmt_row(plain_rows[0]), sep]
    for row in plain_rows[1:]:
        lines.append(fmt_row(row))
    lines.append(sep)

    table_text = "\n".join(lines)
    return f"<pre>{html.escape(table_text, quote=False)}</pre>"


def _extract_markdown_tables(text):
    """Extract markdown table blocks and convert to HTML table tags.

    Must be called AFTER html.escape + markdown formatting regexes,
    so cell content is already escaped and formatted.
    Table detection relies on pipe chars (|) which survive html.escape.

    Returns: (processed_text, table_protected_dict)
    """
    if not text:
        return text, {}

    lines = text.split("\n")
    protected = {}
    table_id = 0
    i = 0
    result_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line could start a table
        if stripped.startswith("|") and i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            if _is_table_separator_line(next_stripped):
                # Collect all consecutive table rows
                j = i
                while j < len(lines):
                    s = lines[j].strip()
                    if s.startswith("|") and s.endswith("|"):
                        j += 1
                    else:
                        break

                table_lines = lines[i:j]
                html_table = _build_pre_table(table_lines)
                if html_table:
                    placeholder = f"{_PLACEHOLDER_PREFIX}TABLE_{table_id}{_PLACEHOLDER_SUFFIX}"
                    protected[placeholder] = html_table
                    result_lines.append(placeholder)
                    table_id += 1
                    i = j
                    continue

        result_lines.append(line)
        i += 1

    return "\n".join(result_lines), protected


def to_telegram_html(text):
    """
    Convert text to Telegram HTML format (official recommendation).

    Supported formatting:
    - <b>bold</b>
    - <strong>bold</strong>
    - <i>italic</i>
    - <em>italic</em>
    - <u>underline</u>
    - <s>strikethrough</s>
    - <del>strikethrough</del>
    - <tg-spoiler>spoiler</tg-spoiler>
    - <code>inline fixed-width code</code>
    - <pre>pre-formatted code</pre>
    - <pre><code class="language-python">highlighted code</code></pre>
    - <a href="url">inline URL</a>
    - # H1 / ## H2 / ### H3+ → <b>bold</b> with level indicator
    - > blockquote → <blockquote>...</blockquote>
    - Markdown tables → ASCII-art <pre> block (Telegram ignores <table> tags)

    Args:
        text: Raw text with Markdown-like formatting

    Returns:
        HTML-formatted text safe for Telegram API
    """
    if not text:
        return ""

    # 1) Protect markdown code and already-valid Telegram HTML tags
    text, code_protected = _extract_protected_regions(text)
    text, html_tag_protected = _extract_allowed_html_tags(text)

    # 2) Extract markdown links BEFORE html.escape (prevent & in URL from double-escaping)
    text, link_protected = _extract_markdown_links(text)

    # 3) Extract blockquotes BEFORE html.escape (> becomes &gt; after escaping)
    text, blockquote_protected = _extract_blockquotes(text)

    # 4) Escape everything else
    result = html.escape(text, quote=True)

    # 5) Convert markdown headers to bold (# is not affected by html.escape)
    result = _convert_headers(result)

    # 6) Convert remaining markdown-style inline formatting to Telegram HTML
    result = re.sub(r"\*\*\*([^\n]+?)\*\*\*", r"<b><i>\1</i></b>", result)  # bold+italic
    result = re.sub(r"\*\*([^\n]+?)\*\*", r"<b>\1</b>", result)
    result = re.sub(r"__([^\n]+?)__", r"<u>\1</u>", result)
    result = re.sub(r"~~([^\n]+?)~~", r"<s>\1</s>", result)
    result = re.sub(r"\|\|([^\n]+?)\|\|", r"<tg-spoiler>\1</tg-spoiler>", result)
    result = re.sub(r"(?<!\*)\*(?!\*)([^\n]+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", result)

    # 7) Convert markdown tables to pre-formatted ASCII art
    #    Called AFTER html.escape + formatting regexes so cell content is already processed
    result, table_protected = _extract_markdown_tables(result)

    # 8) Restore protected regions in dependency order:
    #    tables → blockquotes (may contain code placeholders) → links → html tags → code
    result = _restore_text_map(result, table_protected)
    blockquote_html = {ph: _render_blockquote_to_html(raw) for ph, raw in blockquote_protected.items()}
    result = _restore_text_map(result, blockquote_html)
    result = _restore_text_map(result, link_protected)
    result = _restore_text_map(result, html_tag_protected)
    code_html = {ph: _render_code_region_to_html(original) for ph, original in code_protected.items()}
    return _restore_text_map(result, code_html)


def to_markdown_v2(text):
    """
    Convert text to Telegram MarkdownV2 format (for fallback when HTML fails).

    Converts standard markdown patterns to Telegram MDV2 equivalents:
    - **bold** -> *bold*
    - *italic* -> _italic_
    - ~~strike~~ -> ~strike~
    - __underline__ (preserved)
    - ||spoiler|| (preserved)
    - [text](url) (preserved)

    Only escapes special characters that are not part of valid formatting.
    """
    if not text:
        return ""

    # Protect code blocks and inline code
    text, protected = _extract_protected_regions(text)

    # Process text character by character
    result = []
    i = 0
    while i < len(text):
        # Bold: **text** -> *text*
        if (text[i:i+2] == "**" and
                (i + 2 >= len(text) or text[i+2] != "*") and
                text.find("**", i + 2) != -1):
            end = text.find("**", i + 2)
            if end != -1:
                inner = text[i+2:end]
                result.append("*")
                result.append(_escape_mdv2(inner))
                result.append("*")
                i = end + 2
                continue

        # Italic: *text* -> _text_
        if (text[i] == "*" and
                not (i + 1 < len(text) and text[i+1] == "*") and
                text.find("*", i + 1) != -1):
            end = text.find("*", i + 1)
            if end != -1 and (end + 1 >= len(text) or text[end+1] != "*"):
                inner = text[i+1:end]
                result.append("_")
                result.append(_escape_mdv2(inner))
                result.append("_")
                i = end + 1
                continue

        # Strikethrough: ~~text~~ -> ~text~
        if text[i:i+2] == "~~":
            end = text.find("~~", i + 2)
            if end != -1:
                inner = text[i+2:end]
                result.append("~")
                result.append(_escape_mdv2(inner))
                result.append("~")
                i = end + 2
                continue

        # Underline: __text__ (same syntax in MDV2)
        if text[i:i+2] == "__":
            end = text.find("__", i + 2)
            if end != -1:
                inner = text[i+2:end]
                result.append("__")
                result.append(_escape_mdv2(inner))
                result.append("__")
                i = end + 2
                continue

        # Spoiler: ||text|| (same syntax in MDV2)
        if text[i:i+2] == "||":
            end = text.find("||", i + 2)
            if end != -1:
                inner = text[i+2:end]
                result.append("||")
                result.append(_escape_mdv2(inner))
                result.append("||")
                i = end + 2
                continue

        # Link: [text](url) (same syntax in MDV2, escape url)
        if text[i] == "[":
            close_bracket = text.find("]", i)
            if (close_bracket != -1 and
                    close_bracket + 1 < len(text) and
                    text[close_bracket + 1] == "("):
                close_paren = text.find(")", close_bracket + 2)
                if close_paren != -1:
                    link_text = text[i+1:close_bracket]
                    link_url = text[close_bracket+2:close_paren]
                    result.append("[")
                    result.append(_escape_mdv2(link_text))
                    result.append("](")
                    result.append(_escape_mdv2(link_url))
                    result.append(")")
                    i = close_paren + 1
                    continue

        # Regular character - escape if MDV2 special
        if text[i] in _MDV2_SPECIAL_CHARS:
            result.append("\\" + text[i])
        else:
            result.append(text[i])
        i += 1

    result = "".join(result)

    # Fix placeholders that got their _ escaped (e.g. \x00CODEBLOCK\_0\x00 -> \x00CODEBLOCK_0\x00)
    for ph, original in protected.items():
        # The placeholder key (ph) is what was used as \x00CODEBLOCK_0\x00 in the text
        # It may have had its _ inside the label escaped to \_
        escaped_ph = ph.replace("_", "\\_")
        if escaped_ph != ph:
            result = result.replace(escaped_ph, ph)

    # Restore protected code blocks and inline code
    result = _restore_protected_regions(result, protected)

    return result


def safe_format(text, prefer_html=True):
    """
    Main entry point for formatting text for Telegram.

    Strategy:
    1. Try HTML format (official recommendation, simpler escaping)
    2. If HTML has issues, use MarkdownV2 as fallback
    3. Return tuple: (formatted_text, parse_mode)

    Args:
        text: Raw text to format
        prefer_html: If True, return HTML-first result; if False, return MD-only result

    Returns:
        Tuple[str, ParseMode]: (formatted_text, parse_mode_constant)
    """
    if not text:
        return "", ParseMode.HTML

    if prefer_html:
        html_text = to_telegram_html(text)
        return html_text, ParseMode.HTML
    else:
        md_text = to_markdown_v2(text)
        return md_text, ParseMode.MARKDOWN_V2


def get_parse_mode_for_fallback(current_mode):
    """Get fallback parse mode when current mode fails."""
    if current_mode == ParseMode.HTML:
        return ParseMode.MARKDOWN_V2
    elif current_mode == ParseMode.MARKDOWN_V2:
        return None  # No parse mode = plain text fallback
    return None
