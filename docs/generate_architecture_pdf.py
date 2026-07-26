"""Generate a printable architecture diagram for the Twilio messaging flow."""

from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas


OUT = Path(__file__).with_name("twilio-ai-support-architecture.pdf")

INK = HexColor("#1A2332")
MUTED = HexColor("#5A6577")
LINE = HexColor("#2F3B4F")
BOX_FILL = HexColor("#F4F7FB")
ACCENT = HexColor("#0B6E4F")
ACCENT_SOFT = HexColor("#D8EFE6")
WARN = HexColor("#8A5A00")
WARN_SOFT = HexColor("#FFF1D6")
TWILIO = HexColor("#F22F46")
TWILIO_SOFT = HexColor("#FDE7EA")


def round_box(c, x, y, w, h, fill, stroke, radius=10):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.5)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def title(c, text, x, y, size=11, color=INK, bold=True):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, text)


def body(c, text, x, y, size=8.5, color=MUTED):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.drawCentredString(x, y, text)


def arrow(c, x1, y1, x2, y2, label="", color=LINE, dashed=False):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.8)
    if dashed:
        c.setDash(4, 3)
    else:
        c.setDash()
    c.line(x1, y1, x2, y2)
    c.setDash()

    # arrow head
    import math

    angle = math.atan2(y2 - y1, x2 - x1)
    size = 8
    ax = x2 - size * math.cos(angle - 0.4)
    ay = y2 - size * math.sin(angle - 0.4)
    bx = x2 - size * math.cos(angle + 0.4)
    by = y2 - size * math.sin(angle + 0.4)
    path = c.beginPath()
    path.moveTo(x2, y2)
    path.lineTo(ax, ay)
    path.lineTo(bx, by)
    path.close()
    c.drawPath(path, fill=1, stroke=0)

    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 + 8
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(mx, my, label)


def draw():
    width, height = landscape(letter)
    c = canvas.Canvas(str(OUT), pagesize=landscape(letter))

    # Header
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(36, height - 42, "AI Customer Support Agent — Messaging Architecture")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(
        36,
        height - 60,
        "How Twilio (RCS/SMS) talks to your app — and how your AI replies",
    )

    # Legend strip
    round_box(c, 36, height - 108, width - 72, 34, ACCENT_SOFT, ACCENT, radius=8)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, height - 88, "Read left → right for inbound. Bottom dashed arrow is the reply path.")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawString(
        50,
        height - 102,
        "Inbound = Twilio pushes a webhook to you.  Outbound = your app calls Twilio’s API.",
    )

    # Row of main boxes
    box_w, box_h = 145, 110
    y = height - 260
    gap = 28
    start_x = 36
    boxes = []

    labels = [
        (
            "1. Customer",
            "Phone / RCS chat",
            "Sends a support message",
            BOX_FILL,
            LINE,
        ),
        (
            "2. Twilio",
            "Messaging platform",
            "Receives RCS/SMS; routes it",
            TWILIO_SOFT,
            TWILIO,
        ),
        (
            "3. Your App (API)",
            "FastAPI webhook endpoint",
            "e.g. POST /webhooks/twilio",
            BOX_FILL,
            LINE,
        ),
        (
            "4. AI Agent",
            "Reason + knowledge + tools",
            "Decide answer or escalate",
            ACCENT_SOFT,
            ACCENT,
        ),
        (
            "5. Reply via Twilio",
            "Outbound REST API call",
            "Deliver RCS/SMS reply",
            TWILIO_SOFT,
            TWILIO,
        ),
    ]

    for i, (t, s1, s2, fill, stroke) in enumerate(labels):
        x = start_x + i * (box_w + gap)
        boxes.append((x, y, box_w, box_h))
        round_box(c, x, y, box_w, box_h, fill, stroke)
        title(c, t, x + box_w / 2, y + box_h - 28, size=11, color=stroke)
        body(c, s1, x + box_w / 2, y + box_h - 50, size=8.5, color=INK)
        body(c, s2, x + box_w / 2, y + box_h - 66, size=8, color=MUTED)

    # Inbound arrows between boxes 1-4
    for i in range(4):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i + 1][0]
        cy = y + box_h / 2 + 8
        labels_arrow = [
            "message",
            "webhook POST",
            "process",
            "compose reply",
        ]
        # only draw straight inbound for first three; 4->5 is reply direction same row
        if i < 3:
            arrow(c, x1 + 2, cy, x2 - 2, cy, labels_arrow[i], LINE)
        else:
            arrow(c, x1 + 2, cy, x2 - 2, cy, labels_arrow[i], ACCENT)

    # Return path note under boxes 5 -> 1 conceptually via Twilio already shown
    # Local development callout
    callout_y = 70
    round_box(c, 36, callout_y, 360, 95, WARN_SOFT, WARN, radius=10)
    c.setFillColor(WARN)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, callout_y + 72, "Local development tip")
    c.setFillColor(INK)
    c.setFont("Helvetica", 8.5)
    lines = [
        "Your laptop is not on the public internet by default.",
        "Use a secure tunnel (e.g. ngrok) so Twilio can reach:",
        "https://your-tunnel.example → http://localhost:8000/webhooks/twilio",
        "In production, Twilio points at your real HTTPS server URL.",
    ]
    for i, line in enumerate(lines):
        c.drawString(50, callout_y + 54 - i * 13, line)

    # Safety / production box
    round_box(c, 412, callout_y, 350, 95, BOX_FILL, LINE, radius=10)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(426, callout_y + 72, "Production habits (do these early)")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    habits = [
        "Store Twilio credentials in .env — never commit secrets",
        "Validate Twilio webhook signatures (prove requests are real)",
        "Log conversation IDs for audit / support review",
        "Escalate uncertain or high-risk cases to a human",
    ]
    for i, line in enumerate(habits):
        c.drawString(426, callout_y + 54 - i * 13, line)

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(
        36,
        28,
        "AI-Support-Agent  ·  Reference diagram  ·  RCS when available; SMS fallback is a product setting in Twilio",
    )
    c.drawRightString(width - 36, 28, "Page 1 of 3")

    # Second page: sequence for tactile teaching
    c.showPage()
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 42, "Step-by-step: one customer message")

    steps = [
        ("A", "Customer sends a message", "From their phone over RCS (or SMS if RCS is unavailable)."),
        ("B", "Twilio receives it", "Twilio owns carrier delivery. Your app does not talk to carriers directly."),
        ("C", "Twilio calls your webhook", "HTTP POST with From, Body, MessageSid, etc. This is the “push” into your environment."),
        ("D", "Your API accepts the request", "FastAPI endpoint validates signature, parses the payload, starts a conversation turn."),
        ("E", "AI Agent decides what to do", "Look up knowledge, call tools, draft a reply, or escalate to a human."),
        ("F", "Your app calls Twilio to reply", "Outbound REST/SDK send. Twilio delivers RCS/SMS back to the customer."),
    ]

    y_pos = height - 100
    for num, heading, detail in steps:
        round_box(c, 36, y_pos - 48, 48, 48, ACCENT_SOFT, ACCENT, radius=24)
        title(c, num, 60, y_pos - 28, size=14, color=ACCENT)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y_pos - 18, heading)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 10)
        c.drawString(100, y_pos - 36, detail)
        y_pos -= 70

    round_box(c, 36, 48, width - 72, 70, TWILIO_SOFT, TWILIO, radius=10)
    c.setFillColor(TWILIO)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 98, "Remember the two directions")
    c.setFillColor(INK)
    c.setFont("Helvetica", 9.5)
    c.drawString(50, 78, "Inbound:  Twilio  →  your webhook  (they call you)")
    c.drawString(50, 60, "Outbound: your app → Twilio API     (you call them)")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 36, 28, "Page 2 of 3")

    # Third page: RCS → SMS fallback
    c.showPage()
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(36, height - 42, "RCS → SMS fallback (one page)")

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 10)
    c.drawString(
        36,
        height - 60,
        "RCS is richer messaging. SMS is the reliable backup. Your AI should assume either path can deliver the reply.",
    )

    # Decision flow boxes
    flow_y = height - 200
    flow_boxes = [
        (36, "Your app sends", "One outbound request\nto Twilio", BOX_FILL, LINE),
        (200, "Twilio decides", "Can this device /\ncarrier take RCS?", TWILIO_SOFT, TWILIO),
        (364, "Path A: RCS", "Rich cards, media,\nbuttons / actions", ACCENT_SOFT, ACCENT),
        (528, "Path B: SMS", "Plain text fallback\n(limited formatting)", WARN_SOFT, WARN),
    ]
    for x, heading, detail, fill, stroke in flow_boxes:
        round_box(c, x, flow_y, 140, 90, fill, stroke)
        title(c, heading, x + 70, flow_y + 62, size=10, color=stroke)
        for i, line in enumerate(detail.split("\n")):
            body(c, line, x + 70, flow_y + 42 - i * 14, size=8.5, color=INK)

    # Arrows: app -> Twilio, then Twilio branches
    arrow(c, 176, flow_y + 45, 200, flow_y + 45, "", LINE)
    arrow(c, 340, flow_y + 55, 364, flow_y + 55, "if yes", ACCENT)
    arrow(c, 340, flow_y + 35, 364, flow_y + 35, "", WARN)
    # visual hint for branch down to SMS - draw a small label
    c.setFillColor(WARN)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(342, flow_y + 18, "if no →")

    # Why fallback happens
    round_box(c, 36, flow_y - 145, 350, 120, BOX_FILL, LINE, radius=10)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, flow_y - 40, "Why fallback happens")
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    why_lines = [
        "• Device does not support RCS",
        "• Carrier / region has no RCS path",
        "• Customer has RCS disabled",
        "• Temporary delivery failure on RCS",
        "• Sender / Messaging Service not RCS-ready",
    ]
    for i, line in enumerate(why_lines):
        c.drawString(50, flow_y - 60 - i * 14, line)

    # Product implications for the AI
    round_box(c, 402, flow_y - 145, 360, 120, ACCENT_SOFT, ACCENT, radius=10)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(416, flow_y - 40, "What this means for your AI agent")
    c.setFont("Helvetica", 9)
    c.setFillColor(INK)
    ai_lines = [
        "• Prefer clear plain-text answers first",
        "• Treat buttons / rich cards as optional UX",
        "• Never put critical info only in a button",
        "• Keep replies short enough for SMS",
        "• Log channel used (RCS vs SMS) when available",
    ]
    for i, line in enumerate(ai_lines):
        c.drawString(416, flow_y - 60 - i * 14, line)

    # Bottom rule of thumb
    round_box(c, 36, 48, width - 72, 78, WARN_SOFT, WARN, radius=10)
    c.setFillColor(WARN)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, 106, "Rule of thumb")
    c.setFillColor(INK)
    c.setFont("Helvetica", 9.5)
    c.drawString(
        50,
        86,
        "Your app usually sends once. Twilio (plus Messaging Service settings) chooses RCS when possible and SMS when not.",
    )
    c.drawString(
        50,
        68,
        "Design the support experience so SMS-only customers still get a complete, safe answer — then enhance with RCS when available.",
    )

    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(
        36,
        28,
        "AI-Support-Agent  ·  Fallback reference  ·  Exact Twilio knobs live in Messaging Service / sender configuration",
    )
    c.drawRightString(width - 36, 28, "Page 3 of 3")

    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    draw()
