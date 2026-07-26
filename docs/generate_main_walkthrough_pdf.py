"""Generate a printable plain-English walkthrough of app/main.py."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


OUT = Path(__file__).with_name("main-py-line-by-line.pdf")

INK = HexColor("#1A2332")
MUTED = HexColor("#5A6577")
LINE = HexColor("#2F3B4F")
BOX_FILL = HexColor("#F4F7FB")
ACCENT = HexColor("#0B6E4F")
ACCENT_SOFT = HexColor("#D8EFE6")
CODE_BG = HexColor("#EEF2F6")
CODE = HexColor("#0F3D68")

# (line_number, code_snippet, plain_english)
# Blank / comment lines included so the walkthrough matches the file.
LINES = [
    (
        1,
        "from config import print_openai_key_status",
        "Borrow one tool from config.py: a function that checks whether your API key loaded — without printing the secret.",
    ),
    (
        2,
        "from support import (",
        "Start borrowing several tools and labels from support.py. The opening parenthesis means “this import list continues on the next lines.”",
    ),
    (
        3,
        "ACCOUNT_HELP,",
        "Bring in the category label for account problems (login, password, profile).",
    ),
    (
        4,
        "ESCALATION,",
        "Bring in the category for “hand this to a human / nothing else fits.”",
    ),
    (
        5,
        "ORDER_HELP,",
        "Bring in the category for shipping, tracking, and order status questions.",
    ),
    (
        6,
        "PRODUCT_QUESTIONS,",
        "Bring in the category for product features, materials, sizes, and how things work.",
    ),
    (
        7,
        "RETURNS_REFUNDS_COMPLAINTS,",
        "Bring in the category for returns, refunds, and unhappy customers.",
    ),
    (
        8,
        "SLEEP_DISCLAIMER,",
        "Bring in the ready-made “this is not medical advice” sentence for sleep guidance.",
    ),
    (
        9,
        "SLEEP_GUIDANCE,",
        "Bring in the category for general better-sleep tips and habits.",
    ),
    (
        10,
        "category_label,",
        "Bring in a helper that turns a machine code (like sleep_guidance) into a readable name.",
    ),
    (
        11,
        "classify_request,",
        "Bring in the classifier: the function that reads the customer question and picks a category.",
    ),
    (
        12,
        ")",
        "End of the import list from support.py.",
    ),
    (
        13,
        "(blank line)",
        "Blank lines are ignored by Python. We use them so humans can read the file more easily.",
    ),
    (
        14,
        'print("=" * 40)',
        "Print a banner line of 40 equal signs. '=' * 40 means “repeat this character 40 times.”",
    ),
    (
        15,
        'print(" AI Support Agent — Better Sleep")',
        "Print the app title so you know the program started.",
    ),
    (
        16,
        'print("=" * 40)',
        "Print the matching bottom banner line for the title block.",
    ),
    (
        17,
        "(blank line)",
        "Visual spacing before the next section.",
    ),
    (
        18,
        "# Prove the secret loaded...",
        "A comment (starts with #). Python ignores it. It explains intent to future-you.",
    ),
    (
        19,
        "print()",
        "Print an empty line — just spacing in the terminal output.",
    ),
    (
        20,
        "key_ok = print_openai_key_status()",
        "Call the key-check function. It prints a safe status message and returns True/False into key_ok.",
    ),
    (
        21,
        "if not key_ok:",
        "If the key did NOT look good, run the indented block under this line. not flips True↔False.",
    ),
    (
        22,
        'print("Fix .env before...")',
        "Warn yourself that .env needs fixing before live AI replies will work.",
    ),
    (
        23,
        "print()",
        "Another blank line for readable terminal output.",
    ),
    (
        24,
        "(blank line)",
        "Spacing in the source file before we ask the customer question.",
    ),
    (
        25,
        'question = input("How can I help...")',
        "Ask the user a question in the terminal, wait for typing, store their answer in question.",
    ),
    (
        26,
        "(blank line)",
        "Spacing before we echo the question back.",
    ),
    (
        27,
        'print(f"\\nYou asked: {question}")',
        "Print what they typed. The f before the quote means “fill in {question} with the real text.” \\n starts a new line.",
    ),
    (
        28,
        "(blank line)",
        "Spacing before classification.",
    ),
    (
        29,
        "category = classify_request(question)",
        "Send the question to the classifier. Store the result code (e.g. order_help) in category.",
    ),
    (
        30,
        "label = category_label(category)",
        "Convert that code into a friendly label (e.g. “Order Help”) for display.",
    ),
    (
        31,
        "(blank line)",
        "Spacing before printing the classification.",
    ),
    (
        32,
        'print(f"\\nClassified as: {label}")',
        "Show which support lane we chose, using the friendly label.",
    ),
    (
        33,
        "(blank line)",
        "Spacing before the response section.",
    ),
    (
        34,
        "# Temporary responses...",
        "Comment: these replies are placeholders until AI drafting is wired up.",
    ),
    (
        35,
        "# Real drafted answers...",
        "Comment: reminds us the next milestone is AI-written replies.",
    ),
    (
        36,
        "if category == SLEEP_GUIDANCE:",
        "First branch: if this is sleep guidance, run the indented lines under this if.",
    ),
    (
        37,
        'print("\\n" + SLEEP_DISCLAIMER)',
        "Print a blank line, then the medical/wellness disclaimer (required for sleep advice).",
    ),
    (
        38,
        'print("\\nI can share general...")',
        "Print a short placeholder reply for sleep guidance.",
    ),
    (
        39,
        "elif category == ORDER_HELP:",
        "Else-if: only checked if the previous if was false. Handles order questions.",
    ),
    (
        40,
        'print("\\nI can help with your order...")',
        "Placeholder reply asking for an order number.",
    ),
    (
        41,
        "elif category == PRODUCT_QUESTIONS:",
        "Next branch for product questions.",
    ),
    (
        42,
        'print("\\nI can help with product...")',
        "Placeholder reply for product help.",
    ),
    (
        43,
        "elif category == ACCOUNT_HELP:",
        "Next branch for account/login help.",
    ),
    (
        44,
        'print("\\nI can help with account...")',
        "Placeholder reply pointing at password reset.",
    ),
    (
        45,
        "elif category == RETURNS_REFUNDS_COMPLAINTS:",
        "Next branch for returns, refunds, and complaints.",
    ),
    (
        46,
        'print("\\nI can help start a return...")',
        "Placeholder reply for that sensitive category.",
    ),
    (
        47,
        "elif category == ESCALATION:",
        "Final branch: escalate when nothing else fits or the customer needs a human.",
    ),
    (
        48,
        'print("\\nI want to make sure...")',
        "Empathetic escalation message (part 1).",
    ),
    (
        49,
        'print("I am escalating...")',
        "Escalation message (part 2): handoff language.",
    ),
    (
        50,
        "(end of file)",
        "When Python finishes the last line, the program ends (unless waiting on input earlier).",
    ),
]


def wrap(text: str, width: int = 92) -> list[str]:
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


def draw_header(c, width, height, page_num, page_count):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "main.py — Plain-English Line-by-Line Guide")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(
        40,
        height - 56,
        "AI Support Agent (Better Sleep)  ·  Read with the code open beside you",
    )
    c.drawRightString(width - 40, height - 56, f"Page {page_num} of {page_count}")

    c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.line(40, height - 66, width - 40, height - 66)


def draw():
    width, height = letter
    c = canvas.Canvas(str(OUT), pagesize=letter)

    # Estimate pages: cover + entries
    # We'll paginate dynamically.
    y = height - 90
    page_num = 1
    # Pre-count pages with a dry run
    pages_content: list[list] = [[]]
    temp_y = height - 90

    def entry_height(code: str, english: str) -> float:
        code_lines = wrap(code, 78)
        eng_lines = wrap(english, 88)
        return 18 + 11 * len(code_lines) + 11 * len(eng_lines) + 10

    for item in LINES:
        h = entry_height(item[1], item[2])
        if temp_y - h < 50:
            pages_content.append([])
            temp_y = height - 90
        pages_content[-1].append(item)
        temp_y -= h

    page_count = len(pages_content) + 1  # + overview page

    # ---- Overview page ----
    draw_header(c, width, height, 1, page_count)

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, height - 95, "What this file does (big picture)")

    overview = [
        "main.py is the front door of your app. When you run it, Python starts at the top and",
        "walks downward, one statement at a time.",
        "",
        "In plain English, today’s main.py does four jobs:",
        "  1) Import helpers from other files (config.py and support.py)",
        "  2) Show a title and confirm the API key loaded safely",
        "  3) Ask the customer a question and classify it into one of 6 lanes",
        "  4) Print a temporary reply for that lane (AI replies come next)",
        "",
        "Professional habit: keep main.py thin. It should orchestrate — call helpers — not",
        "contain all business rules. Classification lives in support.py; secrets live in .env",
        "and are loaded via config.py.",
    ]
    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    y = height - 118
    for line in overview:
        c.drawString(40, y, line)
        y -= 14

    # Mini flow box
    c.setFillColor(ACCENT_SOFT)
    c.setStrokeColor(ACCENT)
    c.roundRect(40, 120, width - 80, 110, 10, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, 205, "Flow while the program runs")
    c.setFillColor(INK)
    c.setFont("Helvetica", 9.5)
    flow = [
        "Start → import tools → print banner → check API key → ask question",
        "→ classify_request(question) → category_label(category)",
        "→ if / elif chain picks a temporary reply → program ends",
    ]
    fy = 180
    for line in flow:
        c.drawString(55, fy, line)
        fy -= 16

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(40, 40, "Tip: keep this PDF next to Cursor. Match each line number to the editor gutter.")
    c.showPage()

    # ---- Line pages ----
    for page_index, items in enumerate(pages_content, start=2):
        draw_header(c, width, height, page_index, page_count)
        y = height - 90

        for line_no, code, english in items:
            needed = entry_height(code, english)
            if y - needed < 45:
                break

            # Line number badge
            c.setFillColor(ACCENT_SOFT)
            c.setStrokeColor(ACCENT)
            c.roundRect(40, y - 4, 36, 16, 4, fill=1, stroke=1)
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(58, y, str(line_no) if isinstance(line_no, int) else "—")

            # Code
            c.setFillColor(CODE_BG)
            c.roundRect(84, y - 6, width - 124, 18, 4, fill=1, stroke=0)
            c.setFillColor(CODE)
            c.setFont("Courier", 8)
            code_display = code if len(code) < 86 else code[:83] + "..."
            c.drawString(90, y, code_display)

            y -= 22

            # Plain English
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Bold", 8)
            c.drawString(84, y, "Plain English:")
            c.setFillColor(INK)
            c.setFont("Helvetica", 9)
            y -= 12
            for wrapped in wrap(english, 88):
                c.drawString(84, y, wrapped)
                y -= 11

            y -= 10

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(40, 36, "AI-Support-Agent  ·  Study sheet for app/main.py")
        if page_index < page_count:
            c.showPage()

    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    draw()
