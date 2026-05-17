#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Obsidian Book Source Enricher for Codex Vitae.

Safe-by-default:
- scans only Markdown files under 03.Library/Books
- queries public book metadata APIs with rate limiting
- scan/preview only write timestamped reports under memory/book_enricher_reports
- apply requires --confirm, fills missing MVP metadata only, creates .bak_book_enricher backups
- never edits protected reading/curation fields such as status, rating, tags, aliases, type, category, source_book
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

VAULT = Path(r"D:\Documents_Learn\Personal\Obsidian\Codex Vitae")
BOOKS_DIR = VAULT / "03.Library" / "Books"
REPORT_DIR = Path(__file__).resolve().parent / "book_enricher_reports"

USER_AGENT = "CodexVitaeBookEnricher/0.1 (+private library metadata preview)"
REQUEST_TIMEOUT = 18
REQUEST_INTERVAL = 0.8

PROTECTED_FIELDS = {"status", "rating", "reading_status", "started_reading", "finished_reading", "started", "finished"}
FILL_FIELDS = ["title", "author", "publisher", "year", "pages", "isbn", "source"]


@dataclass
class BookRecord:
    path: str
    name: str
    frontmatter: dict[str, Any]
    missing: list[str]


@dataclass
class Candidate:
    provider: str
    title: str | None = None
    authors: list[str] | None = None
    publisher: str | None = None
    year: int | None = None
    pages: int | None = None
    isbn: str | None = None
    url: str | None = None
    confidence: float = 0.0
    raw_id: str | None = None


def setup_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, text
    normalized = text.replace("\r\n", "\n")
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2]
    return parse_simple_yaml(fm_text), body


def parse_simple_yaml(fm_text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = fm_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line or line.startswith(" "):
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            # collect simple list block
            block: list[str] = []
            j = i + 1
            while j < len(lines) and (lines[j].startswith("  - ") or lines[j].strip() == ""):
                if lines[j].startswith("  - "):
                    block.append(unquote_scalar(lines[j][4:].strip()))
                j += 1
            data[key] = block if block else None
            i = j
            continue
        data[key] = parse_scalar(value)
        i += 1
    return data


def parse_scalar(value: str) -> Any:
    if value in {"null", "~"}:
        return None
    if value in {"''", '""'}:
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    return unquote_scalar(value)


def unquote_scalar(value: str) -> str:
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
        return value[1:-1]
    return value


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def load_book_record(path: Path) -> BookRecord:
    text = path.read_text(encoding="utf-8")
    fm, _body = parse_frontmatter(text)
    title = fm.get("title") or path.stem
    missing = [field for field in FILL_FIELDS if is_empty(fm.get(field))]
    return BookRecord(str(path), str(title), fm, missing)


def scan_books(file_path: str | None = None) -> list[BookRecord]:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Book file not found: {path}")
        return [load_book_record(path)]

    records: list[BookRecord] = []
    for path in sorted(BOOKS_DIR.glob("*.md")):
        if path.name == "Library Catalog.md" or path.name.startswith("."):
            continue
        records.append(load_book_record(path))
    return records


def http_json(url: str) -> dict[str, Any] | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)
    except Exception as exc:
        return {"_error": str(exc), "_url": url}


def first_isbn(volume_info: dict[str, Any]) -> str | None:
    for item in volume_info.get("industryIdentifiers") or []:
        ident = item.get("identifier")
        if ident:
            return str(ident)
    return None


def year_from_date(value: str | None) -> int | None:
    if not value:
        return None
    m = re.search(r"(\d{4})", value)
    return int(m.group(1)) if m else None


def title_similarity(a: str, b: str) -> float:
    def norm(s: str) -> str:
        return re.sub(r"\W+", "", s.lower())
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.82
    seq = SequenceMatcher(None, na, nb).ratio()
    common = len(set(na) & set(nb)) / max(len(set(na) | set(nb)), 1)
    return round(min(0.78, max(seq, common)), 2)


TITLE_HINTS = {
    "CSAPP": "Computer Systems A Programmer's Perspective",
    "DDIA": "Designing Data-Intensive Applications",
    "SICP": "Structure and Interpretation of Computer Programs",
}


def clean_isbn(value: Any) -> str | None:
    if is_empty(value):
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", str(value))
    return cleaned or None


def search_title(book: BookRecord) -> str:
    title = str(book.frontmatter.get("title") or book.name)
    return TITLE_HINTS.get(title, title)


def author_similarity(expected: str | None, candidates: list[str] | None) -> float:
    if not expected:
        return 0.5
    if not candidates:
        return 0.0
    expected_parts = [p.strip() for p in re.split(r"[,;、/&]| and ", expected) if p.strip()]
    if not expected_parts:
        return 0.5
    scores: list[float] = []
    for exp in expected_parts:
        best = max((title_similarity(exp, cand) for cand in candidates), default=0.0)
        scores.append(best)
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def candidate_score(book: BookRecord, candidate_title: str | None, candidate_authors: list[str] | None = None, year: int | None = None) -> float:
    title_score = title_match_score(book, candidate_title)
    author_score = author_similarity(str(book.frontmatter.get("author") or "").strip() or None, candidate_authors)
    score = title_score
    if book.frontmatter.get("author"):
        score = (title_score * 0.72) + (author_score * 0.28)
    # Existing year in the note is treated as a soft constraint; do not trust
    # very old first-publish years for modern technical editions.
    expected_year = book.frontmatter.get("year")
    if isinstance(expected_year, int) and year and abs(expected_year - year) > 3:
        score -= 0.18
    return round(max(0.0, min(1.0, score)), 2)


def title_match_score(book: BookRecord, candidate_title: str | None) -> float:
    title = str(book.frontmatter.get("title") or book.name)
    expanded = search_title(book)
    scores = [title_similarity(title, candidate_title or "")]
    if expanded != title:
        scores.append(title_similarity(expanded, candidate_title or ""))
    return max(scores)


def query_google(book: BookRecord) -> list[Candidate]:
    fm = book.frontmatter
    isbn = clean_isbn(fm.get("isbn"))
    title = search_title(book)
    if isbn:
        query = f"isbn:{isbn}"
    else:
        author = str(fm.get("author") or "").strip()
        query = f'intitle:"{title}" {author}'.strip()
    url = "https://www.googleapis.com/books/v1/volumes?q=" + urllib.parse.quote(str(query)) + "&maxResults=5"
    data = http_json(url)
    if not data or data.get("_error"):
        return [Candidate(provider="google_books", title=None, confidence=0.0, raw_id=data.get("_error") if data else "no data")]
    out: list[Candidate] = []
    for item in data.get("items") or []:
        info = item.get("volumeInfo") or {}
        title = info.get("title")
        score = candidate_score(book, title, info.get("authors") or [], year_from_date(info.get("publishedDate")))
        if isbn:
            score = max(score, 0.9)
        c = Candidate(
            provider="google_books",
            title=title,
            authors=info.get("authors") or [],
            publisher=info.get("publisher"),
            year=year_from_date(info.get("publishedDate")),
            pages=info.get("pageCount"),
            isbn=first_isbn(info),
            url=info.get("canonicalVolumeLink") or info.get("infoLink"),
            confidence=round(score, 2),
            raw_id=item.get("id"),
        )
        out.append(c)
    return out


def query_openlibrary(book: BookRecord) -> list[Candidate]:
    fm = book.frontmatter
    isbn = clean_isbn(fm.get("isbn"))
    if isbn:
        q = "isbn:" + isbn
    else:
        q = f'title:"{search_title(book)}"'
        if fm.get("author"):
            q += f' author:"{fm.get("author")}"'
    url = "https://openlibrary.org/search.json?q=" + urllib.parse.quote(q) + "&limit=5"
    data = http_json(url)
    if not data or data.get("_error"):
        return [Candidate(provider="openlibrary", title=None, confidence=0.0, raw_id=data.get("_error") if data else "no data")]
    out: list[Candidate] = []
    for doc in data.get("docs") or []:
        title = doc.get("title")
        isbn_list = doc.get("isbn") or []
        score = candidate_score(book, title, doc.get("author_name") or [], doc.get("first_publish_year"))
        c = Candidate(
            provider="openlibrary",
            title=title,
            authors=doc.get("author_name") or [],
            publisher=(doc.get("publisher") or [None])[0],
            year=doc.get("first_publish_year"),
            pages=None,
            isbn=isbn_list[0] if isbn_list else None,
            url=("https://openlibrary.org" + doc.get("key")) if doc.get("key") else None,
            confidence=round(score, 2),
            raw_id=doc.get("key"),
        )
        out.append(c)
    return out


def parse_douban_abstract(value: str | None) -> tuple[list[str], str | None, int | None, str | None]:
    """Parse Douban search abstract like: 作者 / 出版社 / 2019-11 / 78.00."""
    if not value:
        return [], None, None, None
    parts = [p.strip() for p in str(value).split("/") if p.strip()]
    authors: list[str] = []
    publisher: str | None = None
    year: int | None = None
    price: str | None = None
    if parts:
        authors = [p.strip() for p in re.split(r"[,;、&]| and ", parts[0]) if p.strip()]
    if len(parts) >= 2:
        publisher = parts[1]
    for part in parts[2:]:
        if year is None:
            year = year_from_date(part)
        if re.search(r"\d+(?:\.\d+)?", part):
            price = part
    return authors, publisher, year, price


def clean_html_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<.*?>", "", value, flags=re.S)
    return html.unescape(value).strip()


def parse_douban_info_block(html_text: str) -> dict[str, str]:
    m = re.search(r'<div[^>]+id=["\']info["\'][^>]*>(.*?)</div>', html_text, re.S | re.I)
    if not m:
        return {}
    text = clean_html_text(m.group(1))
    info: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        mm = re.match(r"^([^:：]+)[:：]\s*(.*)$", line)
        if mm:
            current_key = mm.group(1).strip()
            info[current_key] = mm.group(2).strip()
        elif current_key and not info[current_key]:
            info[current_key] = line
    return info


def parse_int(value: str | None) -> int | None:
    if not value:
        return None
    m = re.search(r"\d+", value)
    return int(m.group(0)) if m else None


def enrich_douban_detail(url_value: str | None) -> dict[str, Any]:
    if not url_value or "book.douban.com/subject/" not in url_value:
        return {}
    req = urllib.request.Request(url_value, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            html_text = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return {}
    info = parse_douban_info_block(html_text)
    isbn = clean_isbn(info.get("ISBN"))
    return {
        "authors": [p.strip() for p in re.split(r"[,;、/]| and ", info.get("作者", "")) if p.strip()],
        "publisher": info.get("出版社") or None,
        "year": year_from_date(info.get("出版年")),
        "pages": parse_int(info.get("页数")),
        "isbn": isbn,
    }


def query_douban_search(book: BookRecord) -> list[Candidate]:
    """Query Douban subject search page and parse embedded window.__DATA__."""
    query = search_title(book)
    url = "https://search.douban.com/book/subject_search?search_text=" + urllib.parse.quote(query) + "&cat=1001"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            html_text = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return [Candidate(provider="douban_search", title=None, confidence=0.0, raw_id=str(exc))]

    m = re.search(r"window\.__DATA__\s*=\s*(\{.*?\});\s*\n\s*window\.__USER__", html_text, re.S)
    if not m:
        return [Candidate(provider="douban_search", title=None, confidence=0.0, raw_id="window.__DATA__ not found")]
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        return [Candidate(provider="douban_search", title=None, confidence=0.0, raw_id=f"json decode: {exc}")]

    out: list[Candidate] = []
    for item in data.get("items") or []:
        title = item.get("title")
        authors, publisher, year, _price = parse_douban_abstract(item.get("abstract"))
        url_value = item.get("url") or ("https://book.douban.com/subject/" + str(item.get("id")) + "/" if item.get("id") else None)
        detail = enrich_douban_detail(url_value)
        authors = detail.get("authors") or authors
        publisher = detail.get("publisher") or publisher
        year = detail.get("year") or year
        pages = detail.get("pages")
        isbn = detail.get("isbn")
        score = candidate_score(book, title, authors, year)
        out.append(Candidate(
            provider="douban_search",
            title=title,
            authors=authors,
            publisher=publisher,
            year=year,
            pages=pages,
            isbn=isbn,
            url=url_value,
            confidence=round(score, 2),
            raw_id=str(item.get("id")) if item.get("id") else None,
        ))
        time.sleep(REQUEST_INTERVAL)
    return out


def best_candidates(book: BookRecord) -> list[Candidate]:
    candidates: list[Candidate] = []
    candidates.extend(query_google(book))
    time.sleep(REQUEST_INTERVAL)
    candidates.extend(query_openlibrary(book))
    time.sleep(REQUEST_INTERVAL)
    candidates.extend(query_douban_search(book))
    filtered = [
        c for c in candidates
        if c.title and c.confidence >= 0.55 and not (c.raw_id and str(c.raw_id).startswith("HTTP Error"))
    ]
    return sorted(filtered, key=lambda c: c.confidence, reverse=True)[:6]


def proposal_threshold(book: BookRecord) -> float:
    # ISBN lookup is strong; fuzzy title lookup needs stricter review.
    return 0.75 if book.frontmatter.get("isbn") else 0.82


def valid_year(value: Any) -> bool:
    if not isinstance(value, int):
        return False
    current_year = dt.datetime.now().year
    return 1450 <= value <= current_year + 1


def valid_pages(value: Any) -> bool:
    if not isinstance(value, int):
        return False
    return 8 <= value <= 3000


def valid_isbn(value: Any) -> bool:
    cleaned = clean_isbn(value)
    return bool(cleaned and len(cleaned) in {10, 13})


def field_value_is_safe(field: str, value: Any) -> bool:
    if field == "year":
        return valid_year(value)
    if field == "pages":
        return valid_pages(value)
    if field == "isbn":
        return valid_isbn(value)
    return True


def propose_fields(book: BookRecord, candidates: list[Candidate]) -> dict[str, dict[str, Any]]:
    proposals: dict[str, dict[str, Any]] = {}
    for field in book.missing:
        if field in PROTECTED_FIELDS:
            continue
        if field == "source":
            for c in candidates:
                if c.confidence < proposal_threshold(book):
                    continue
                if is_empty(c.url):
                    continue
                # Source is a reference link, not a bibliographic fact: prefer the
                # highest-confidence candidate already sorted by best_candidates,
                # instead of provider voting that can promote a wrong duplicate.
                proposals[field] = {"value": c.url, "sources": [c.provider]}
                break
            continue
        values: dict[str, dict[str, Any]] = {}
        for c in candidates:
            if c.confidence < proposal_threshold(book):
                continue
            value: Any = None
            if field == "author" and c.authors:
                value = "、".join(c.authors[:4])
            elif field == "year" and c.provider == "openlibrary" and not (c.publisher or c.isbn or c.pages):
                # OpenLibrary work-level first_publish_year is noisy for classics;
                # use it only when the record has edition-like supporting metadata.
                continue
            else:
                value = getattr(c, field, None)
            if is_empty(value) or not field_value_is_safe(field, value):
                continue
            key = str(value)
            payload = values.setdefault(key, {"providers": [], "best_confidence": 0.0, "first_rank": len(values)})
            payload["providers"].append(c.provider)
            payload["best_confidence"] = max(float(payload["best_confidence"]), c.confidence)
        if values:
            value, payload = sorted(
                values.items(),
                key=lambda kv: (len(set(kv[1]["providers"])), kv[1]["best_confidence"], -kv[1]["first_rank"]),
                reverse=True,
            )[0]
            proposals[field] = {"value": value, "sources": sorted(set(payload["providers"]))}
    return proposals


def format_yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if text == "":
        return "''"
    if re.search(r"[:#\[\]{}&,*!|>'\"%@`]|^\s|\s$", text):
        return json.dumps(text, ensure_ascii=False)
    return text


def split_frontmatter_text(text: str) -> tuple[str, str, str] | None:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None
    parts = normalized.split("---\n", 2)
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]


def apply_proposals_to_text(text: str, proposals: dict[str, dict[str, Any]]) -> str:
    split = split_frontmatter_text(text)
    if split is None:
        raise ValueError("frontmatter not found")
    _prefix, fm_text, body = split
    lines = fm_text.splitlines()
    for field, payload in proposals.items():
        value = payload["value"]
        rendered = f"{field}: {format_yaml_value(value)}"
        replaced = False
        for idx, line in enumerate(lines):
            if re.match(rf"^{re.escape(field)}\s*:", line):
                lines[idx] = rendered
                replaced = True
                break
        if not replaced:
            lines.append(rendered)
    return "---\n" + "\n".join(lines).rstrip() + "\n---\n" + body.lstrip("\n")


def write_book_if_confirmed(book: BookRecord, proposals: dict[str, dict[str, Any]], confirm: bool) -> tuple[bool, str]:
    if not proposals:
        return False, "no proposals"
    if not confirm:
        return False, "dry-run; pass --confirm to write"
    path = Path(book.path)
    if not path.is_file() or BOOKS_DIR not in path.parents:
        return False, "refused: path is outside Books directory"
    text = path.read_text(encoding="utf-8")
    original_fm, _body = parse_frontmatter(text)
    for field in proposals:
        if field in PROTECTED_FIELDS:
            return False, f"refused: protected field {field}"
        if not is_empty(original_fm.get(field)):
            return False, f"refused: field already has value {field}"
    updated = apply_proposals_to_text(text, proposals)
    if updated == text:
        return False, "no text change"
    backup = path.with_suffix(path.suffix + ".bak_book_enricher")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8", newline="\n")
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True, "written; backup kept beside note"


def render_apply(records: list[BookRecord], limit: int | None = None, confirm: bool = False) -> str:
    chosen = records[:limit] if limit else records
    mode = "CONFIRMED WRITE" if confirm else "DRY RUN"
    lines = [
        "# Book Enricher Apply",
        "",
        f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"Mode: {mode}",
        "",
        "> Only missing MVP fields are eligible. Protected reading-state fields are never modified.",
        "",
    ]
    changed = 0
    for idx, r in enumerate(chosen, start=1):
        rel = Path(r.path).relative_to(VAULT)
        lines += [f"## {idx}. {r.name}", "", f"File: `{rel.as_posix()}`", f"Current missing: {', '.join(r.missing) if r.missing else 'none'}", ""]
        if not r.missing:
            lines += ["Result: skipped — no missing MVP fields detected.", ""]
            continue
        candidates = best_candidates(r)
        proposals = propose_fields(r, candidates)
        ok, message = write_book_if_confirmed(r, proposals, confirm)
        if ok:
            changed += 1
        lines += [f"Result: {'updated' if ok else 'skipped'} — {message}", ""]
        if proposals:
            lines += ["### Proposed / applied fills", ""]
            for field, payload in proposals.items():
                lines.append(f"- `{field}`: {payload['value']}  ")
                lines.append(f"  - sources: {', '.join(payload['sources'])}")
            lines.append("")
        else:
            lines += ["### Proposed / applied fills", "", "- none", ""]
        lines += ["### Top candidates", ""]
        for c in candidates[:4]:
            lines.append(f"- {c.provider} | confidence={c.confidence} | {c.title or '(no title)'}")
            if c.authors:
                lines.append(f"  - authors: {'、'.join(c.authors[:4])}")
            if c.publisher or c.year or c.isbn:
                lines.append(f"  - meta: {c.publisher or ''} {c.year or ''} {c.isbn or ''}".strip())
            if c.url:
                lines.append(f"  - url: {c.url}")
        lines.append("")
    lines.insert(6, f"Updated files: {changed}")
    lines.insert(7, "")
    return "\n".join(lines)


def render_scan(records: list[BookRecord]) -> str:
    lines = ["# Book Enricher Scan", "", f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}", "", "> ⚠️ 本工具只填缺失信息源元数据，不验证模板骨架一致性。书页需已按 Book.md 模板创建。若缺模板骨架，请先手工按 `99.System/Templates/Book.md` 重建。", "", f"Books: {len(records)}", ""]
    for r in records:
        rel = Path(r.path).relative_to(VAULT)
        lines += [f"## {r.name}", "", f"File: `{rel.as_posix()}`", f"Missing: {', '.join(r.missing) if r.missing else 'none'}", ""]
    return "\n".join(lines)


def render_preview(records: list[BookRecord], limit: int | None = None) -> str:
    chosen = records[:limit] if limit else records
    lines = ["# Book Enricher Preview", "", f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}", "", "> Preview only. No Vault files were modified.", "", "> ⚠️ 本工具只填缺失信息源元数据，不验证模板骨架一致性。需确保书页已按 Book.md 模板创建。若缺模板骨架，请先手工重建。", ""]
    for idx, r in enumerate(chosen, start=1):
        rel = Path(r.path).relative_to(VAULT)
        lines += [f"## {idx}. {r.name}", "", f"File: `{rel.as_posix()}`", f"Current missing: {', '.join(r.missing) if r.missing else 'none'}", ""]
        if not r.missing:
            lines += ["No missing MVP fields detected.", ""]
            continue
        candidates = best_candidates(r)
        proposals = propose_fields(r, candidates)
        if proposals:
            lines += ["### Proposed fills", ""]
            for field, payload in proposals.items():
                lines.append(f"- `{field}`: {payload['value']}  ")
                lines.append(f"  - sources: {', '.join(payload['sources'])}")
            lines.append("")
        else:
            lines += ["### Proposed fills", "", "- none", ""]
        lines += ["### Top candidates", ""]
        for c in candidates[:4]:
            lines.append(f"- {c.provider} | confidence={c.confidence} | {c.title or '(no title)'}")
            if c.authors:
                lines.append(f"  - authors: {'、'.join(c.authors[:4])}")
            if c.publisher or c.year or c.isbn:
                lines.append(f"  - meta: {c.publisher or ''} {c.year or ''} {c.isbn or ''}".strip())
            if c.url:
                lines.append(f"  - url: {c.url}")
        lines.append("")
    return "\n".join(lines)


def write_report(kind: str, content: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"book_enricher_{kind}_{stamp}.md"
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def main() -> int:
    setup_utf8()
    parser = argparse.ArgumentParser(
        description="Safe preview/apply metadata enrichment for Codex Vitae Books",
        epilog=(
            "Safety: scan/preview only write reports under 99.Meta/reports; "
            "apply requires --confirm, only fills missing fields, preserves protected fields, "
            "and creates .bak_book_enricher backups before modifying book notes."
        ),
    )
    parser.add_argument("command", choices=["scan", "preview", "apply"])
    parser.add_argument("--limit", type=int, default=None, help="limit processed books")
    parser.add_argument("--file", default=None, help="process one specific book markdown file")
    parser.add_argument("--confirm", action="store_true", help="required for apply to modify Vault files")
    args = parser.parse_args()

    records = scan_books(args.file)
    if args.command == "scan":
        path = write_report("scan", render_scan(records))
        print(path)
        return 0
    if args.command == "preview":
        path = write_report("preview", render_preview(records, args.limit))
        print(path)
        return 0
    if args.command == "apply":
        path = write_report("apply", render_apply(records, args.limit, args.confirm))
        print(path)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
