"""
Reusable engine for building plain-English code walkthrough PDFs.

This file knows how to *draw* a walkthrough. It does not know anything about
our support agent. The actual explanations live in generate_walkthroughs.py.

Separating "engine" from "content" means adding a walkthrough for a new file
costs a few lines of text instead of a whole new script.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

DOCS_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = DOCS_DIR / "snapshots"

INK = HexColor("#1A2332")
MUTED = HexColor("#5A6577")
LINE = HexColor("#2F3B4F")
ACCENT = HexColor("#0B6E4F")
ACCENT_SOFT = HexColor("#D8EFE6")
CODE_BG = HexColor("#EEF2F6")
CODE = HexColor("#0F3D68")

PAGE_W, PAGE_H = letter
LEFT = 40
RIGHT = PAGE_W - 40
BADGE_W = 52
TEXT_X = LEFT + BADGE_W + 8
CONTENT_TOP = PAGE_H - 90
CONTENT_BOTTOM = 60


@dataclass
class Entry:
    """One row of the walkthrough: a line (or line range), code, explanation."""

    lines: str
    code: str
    plain_english: str


@dataclass
class Walkthrough:
    """Everything needed to render one PDF."""

    title: str
    subtitle: str
    output_name: str
    overview: list[str]
    flow: list[str]
    entries: list[Entry]
    concepts: list[tuple[str, str]] = field(default_factory=list)


def wrap(text: str, width: int) -> list[str]:
    """Break a long sentence into lines that fit the page width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _header(c, page_num: int, page_count: int, title: str, subtitle: str) -> None:
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(LEFT, PAGE_H - 40, title)

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(LEFT, PAGE_H - 56, subtitle)
    c.drawRightString(RIGHT, PAGE_H - 56, f"Page {page_num} of {page_count}")

    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(LEFT, PAGE_H - 66, RIGHT, PAGE_H - 66)


def _footer(c, note: str) -> None:
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(LEFT, 36, note)


def _entry(c, entry: Entry, y: float, draw: bool) -> float:
    """
    Measure or draw one entry.

    Measuring and drawing share this single function on purpose: if they were
    written separately they could disagree, and the layout would break.
    Returns the vertical space the entry consumes.
    """
    code_lines = wrap(entry.code, 88)
    english_lines = wrap(entry.plain_english, 86)

    box_h = 8 + 11 * len(code_lines)
    top = y

    if draw:
        c.setFillColor(ACCENT_SOFT)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(LEFT, y - box_h + 10, BADGE_W, 16, 4, fill=1, stroke=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(LEFT + BADGE_W / 2, y - box_h + 14, entry.lines)

        c.setFillColor(CODE_BG)
        c.roundRect(TEXT_X, y - box_h + 4, RIGHT - TEXT_X, box_h, 4, fill=1, stroke=0)
        c.setFillColor(CODE)
        c.setFont("Courier", 8)
        cy = y
        for code_line in code_lines:
            c.drawString(TEXT_X + 6, cy, code_line)
            cy -= 11

    y -= box_h + 4

    if draw:
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(TEXT_X, y, "Plain English:")

    y -= 12

    if draw:
        c.setFillColor(INK)
        c.setFont("Helvetica", 9)

    for english_line in english_lines:
        if draw:
            c.drawString(TEXT_X, y, english_line)
        y -= 11

    y -= 10
    return top - y


def _paginate(entries: list[Entry]) -> list[list[Entry]]:
    pages: list[list[Entry]] = [[]]
    y = CONTENT_TOP
    for entry in entries:
        height = _entry(None, entry, y, draw=False)
        if y - height < CONTENT_BOTTOM and pages[-1]:
            pages.append([])
            y = CONTENT_TOP
        pages[-1].append(entry)
        y -= height
    return pages


def _draw_overview(c, walk: Walkthrough, page_count: int) -> None:
    _header(c, 1, page_count, walk.title, walk.subtitle)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, PAGE_H - 95, "What this file does (big picture)")

    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    y = PAGE_H - 118
    for line in walk.overview:
        c.drawString(LEFT, y, line)
        y -= 14

    if walk.concepts:
        y -= 10
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(LEFT, y, "New words you will see in this file")
        y -= 18

        for term, meaning in walk.concepts:
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(LEFT, y, term)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 9)
            for meaning_line in wrap(meaning, 78):
                c.drawString(LEFT + 130, y, meaning_line)
                y -= 12
            y -= 4

    flow_h = 30 + 16 * len(walk.flow)
    c.setFillColor(ACCENT_SOFT)
    c.setStrokeColor(ACCENT)
    c.roundRect(LEFT, 110, RIGHT - LEFT, flow_h, 10, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(LEFT + 15, 110 + flow_h - 22, "Flow while the program runs")
    c.setFillColor(INK)
    c.setFont("Helvetica", 9.5)
    fy = 110 + flow_h - 42
    for line in walk.flow:
        c.drawString(LEFT + 15, fy, line)
        fy -= 16

    _footer(c, "Tip: keep this PDF beside Cursor and match line numbers to the editor gutter.")


def render(walk: Walkthrough, snapshot: bool = False) -> Path:
    """Build the PDF and return where it was written."""
    pages = _paginate(walk.entries)
    page_count = len(pages) + 1

    out_path = DOCS_DIR / walk.output_name
    c = canvas.Canvas(str(out_path), pagesize=letter)

    _draw_overview(c, walk, page_count)
    c.showPage()

    for page_index, page_entries in enumerate(pages, start=2):
        _header(c, page_index, page_count, walk.title, walk.subtitle)
        y = CONTENT_TOP
        for entry in page_entries:
            y -= _entry(c, entry, y, draw=True)
        _footer(c, f"AI-Support-Agent  ·  Study sheet  ·  {walk.subtitle}")
        c.showPage()

    c.save()

    if snapshot:
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        stamped = SNAPSHOT_DIR / f"{date.today().isoformat()}-{walk.output_name}"
        stamped.write_bytes(out_path.read_bytes())

    return out_path
