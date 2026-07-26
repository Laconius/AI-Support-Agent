"""Generate a printable RAG cheat sheet for learning and reference."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = Path(__file__).with_name("rag-cheat-sheet.pdf")

INK = HexColor("#1A2332")
MUTED = HexColor("#5A6577")
LINE = HexColor("#2F3B4F")
ACCENT = HexColor("#0B6E4F")
ACCENT_SOFT = HexColor("#D8EFE6")
BOX = HexColor("#F4F7FB")
WARN = HexColor("#8A5A00")
WARN_SOFT = HexColor("#FFF1D6")
BLUE = HexColor("#0F3D68")
BLUE_SOFT = HexColor("#E7EEF6")
PURPLE = HexColor("#4A3F6B")
PURPLE_SOFT = HexColor("#EEEAF5")


def round_box(c, x, y, w, h, fill, stroke, radius=10):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.4)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def heading(c, text, x, y, size=11, color=INK):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, text)


def body(c, lines, x, y, size=8.5, leading=11, color=MUTED):
    c.setFont("Helvetica", size)
    c.setFillColor(color)
    cursor = y
    for line in lines:
        c.drawString(x, cursor, line)
        cursor -= leading
    return cursor


def draw():
    width, height = letter
    c = canvas.Canvas(str(OUT), pagesize=letter)

    # Header
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 40, "RAG Cheat Sheet — Discrete Concept Compartments")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(
        36,
        height - 56,
        "AI Support Agent (Better Sleep)  ·  Print this. Study one box at a time.",
    )
    c.setStrokeColor(LINE)
    c.line(36, height - 64, width - 36, height - 64)

    # Big idea strip
    round_box(c, 36, height - 118, width - 72, 42, ACCENT_SOFT, ACCENT, radius=8)
    heading(c, "Big idea (one sentence)", 48, height - 88, size=10, color=ACCENT)
    body(
        c,
        [
            "Don't ask the AI to remember your catalog. Retrieve approved facts first, then ask the AI",
            "to write the customer reply using only those facts. That loop is RAG.",
        ],
        48,
        height - 102,
        size=8.5,
        leading=11,
        color=INK,
    )

    # Three pillars R A G
    y = height - 280
    box_w = 168
    gap = 14
    x0 = 36

    pillars = [
        (
            x0,
            BLUE_SOFT,
            BLUE,
            "R — Retrieve",
            "Plain: find the right facts.",
            [
                "In this project:",
                "• knowledge.search_knowledge()",
                "• orders.get_order_help_facts()",
                "",
                "Output = Snippets / OrderHelpFacts",
                "(truth objects, not pretty prose)",
                "",
                "Later: embeddings + vector DB",
                "when docs get large.",
            ],
        ),
        (
            x0 + box_w + gap,
            PURPLE_SOFT,
            PURPLE,
            "A — Augment",
            "Plain: attach facts to the ask.",
            [
                "In this project:",
                "• Build a factual template",
                "• Put FACTS in the prompt",
                "• Pass customer question",
                "• Pass support lane",
                "",
                "Augment = give the model",
                "context it did not train on",
                "(your docs / order record).",
            ],
        ),
        (
            x0 + 2 * (box_w + gap),
            ACCENT_SOFT,
            ACCENT,
            "G — Generate",
            "Plain: write the reply.",
            [
                "In this project:",
                "• responses._warm_rewrite()",
                "• ai_client.complete()",
                "",
                "AI rephrases facts warmly.",
                "If AI fails → template stays.",
                "",
                "Model = writer, not warehouse.",
            ],
        ),
    ]

    for x, fill, stroke, title, plain, lines in pillars:
        round_box(c, x, y, box_w, 150, fill, stroke)
        heading(c, title, x + 10, y + 130, size=11, color=stroke)
        c.setFillColor(INK)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(x + 10, y + 116, plain)
        body(c, lines, x + 10, y + 100, size=8, leading=10, color=INK)

    # Compartment: vs fine-tuning / vs pure LLM
    y2 = 250
    round_box(c, 36, y2, 250, 130, BOX, LINE)
    heading(c, "Compartment: RAG vs guessing", 48, y2 + 110, size=10, color=BLUE)
    body(
        c,
        [
            "Pure LLM alone:",
            "  answers from training memory → can invent",
            "",
            "RAG:",
            "  answers from your retrieved facts → auditable",
            "",
            "Fine-tuning (different tool):",
            "  teaches style/format; still not a live catalog",
            "",
            "We use RAG so product/policy changes = edit docs,",
            "not retrain a model.",
        ],
        48,
        y2 + 94,
        size=8,
        leading=10,
        color=INK,
    )

    round_box(c, 300, y2, 276, 130, BOX, LINE)
    heading(c, "Compartment: our file roles", 312, y2 + 110, size=10, color=ACCENT)
    body(
        c,
        [
            "knowledge.py / orders.py  → RETRIEVE facts",
            "responses.py             → AUGMENT + GENERATE wording",
            "ai_client.py             → talks to OpenAI (connection only)",
            "guardrails.py            → hard safety before/after",
            "support.py               → which lane am I in?",
            "main.py                  → wires the pipeline",
            "",
            "Remember: change docs/data to change truth;",
            "change responses/ai_client to change voice/provider.",
        ],
        312,
        y2 + 94,
        size=8,
        leading=10,
        color=INK,
    )

    # Compartment: glossary
    y3 = 100
    round_box(c, 36, y3, width - 72, 136, WARN_SOFT, WARN)
    heading(c, "Compartment: vocabulary (ruminate here)", 48, y3 + 116, size=10, color=WARN)
    glossary = [
        ("Grounding", "Tying answers to approved sources so claims can be checked."),
        ("Snippet", "One retrieved section from a knowledge doc (our fact unit)."),
        ("Embedding", "A numeric 'meaning fingerprint' of text for similarity search (future)."),
        ("Vector store", "Database of embeddings (Chroma/pgvector) for fast similarity lookup (future)."),
        ("Hallucination", "Model invents a confident-sounding claim not in the facts."),
        ("Faithfulness", "Did the reply stick to retrieved facts? (eval metric later)"),
        ("Warm rewrite", "Our current G step: AI rephrases a factual template more warmly."),
        ("System prompt", "Standing instructions to the model (persona + hard rules)."),
    ]
    col1_x, col2_x = 48, 320
    gy = y3 + 98
    for i, (term, meaning) in enumerate(glossary):
        x = col1_x if i < 4 else col2_x
        if i == 4:
            gy = y3 + 98
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, gy, term)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        # wrap-ish short meanings
        c.drawString(x + 70, gy, meaning[:62])
        if len(meaning) > 62:
            gy -= 9
            c.drawString(x + 70, gy, meaning[62:124])
        gy -= 14

    # Footer roadmap strip
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(
        36,
        48,
        "Roadmap: keyword retrieve (now) → better filters → embeddings/vector DB → hybrid → faithfulness eval → multi-turn state",
    )
    c.drawString(
        36,
        34,
        "AI-Support-Agent  ·  RAG study sheet  ·  One box per sitting beats cramming the whole page.",
    )
    c.drawRightString(width - 36, 34, "1 of 1")

    # Page 2: worked example for this repo
    c.showPage()
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, height - 40, "RAG in this repo — one worked example")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(36, height - 56, "Follow the arrows. Each compartment is one mental step.")
    c.setStrokeColor(LINE)
    c.line(36, height - 64, width - 36, height - 64)

    steps = [
        (
            "1. Customer asks",
            '"Where is order ORD-1001?"',
            "main.py collects the question. Guardrails check input first.",
        ),
        (
            "2. Classify lane",
            "support.classify_request → Order Help",
            "Lane is context we pass forward (prefer the right tools).",
        ),
        (
            "3. Retrieve facts",
            "orders.get_order_help_facts(...)",
            "Truth: status=shipped, tracking=1Z..., ETA=2026-07-24. No prose yet.",
        ),
        (
            "4. Augment",
            "responses builds a factual template + prompt",
            "FACTS block + question + lane go to the model. System prompt bans inventing.",
        ),
        (
            "5. Generate",
            "ai_client.complete(...) warm rewrite",
            "Friendly wording, same numbers. If API fails, template is shown as-is.",
        ),
        (
            "6. Safety net",
            "guardrails.apply_output_guardrails(...)",
            "Blocks refund promises, diagnosis-ish wording, unexpected emails.",
        ),
    ]

    sy = height - 100
    for title, code, plain in steps:
        round_box(c, 36, sy - 52, width - 72, 58, BOX, LINE, radius=8)
        heading(c, title, 48, sy - 8, size=10, color=ACCENT)
        c.setFillColor(BLUE)
        c.setFont("Courier", 8)
        c.drawString(48, sy - 24, code)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        c.drawString(48, sy - 40, plain)
        sy -= 70

    round_box(c, 36, 48, width - 72, 70, ACCENT_SOFT, ACCENT, radius=8)
    heading(c, "Ruminate prompts (pick one)", 48, 100, size=10, color=ACCENT)
    body(
        c,
        [
            "• If I deleted ai_client.py, could the agent still tell the truth? (Yes — templates.)",
            "• If I edited data/knowledge/products.md, would answers change without retraining? (Yes — RAG.)",
            "• If the model 'sounds right' but the tracking number isn't in OrderHelpFacts, what failed? (Grounding.)",
        ],
        48,
        84,
        size=8,
        leading=11,
        color=INK,
    )

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(36, 28, "AI-Support-Agent  ·  RAG worked example")
    c.drawRightString(width - 36, 28, "2 of 2")

    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    draw()
