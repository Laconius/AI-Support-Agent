/**
 * Better Sleep support chat client.
 *
 * Plain idea: type a question in the browser; send it to our API; show the reply.
 * Technical idea: fetch() POST to /v1/support/ask — same door Shopify/Twilio can use later.
 */

const form = document.getElementById("ask-form");
const questionEl = document.getElementById("question");
const sendBtn = document.getElementById("send-btn");
const transcript = document.getElementById("transcript");
const statusEl = document.getElementById("status");

function appendBubble(text, role) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  const p = document.createElement("p");
  p.textContent = text;
  bubble.appendChild(p);
  transcript.appendChild(bubble);
  transcript.scrollTop = transcript.scrollHeight;
}

function appendMeta(text) {
  const meta = document.createElement("div");
  meta.className = "bubble meta";
  meta.textContent = text;
  transcript.appendChild(meta);
  transcript.scrollTop = transcript.scrollHeight;
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  questionEl.disabled = busy;
  statusEl.classList.remove("error");
  statusEl.textContent = busy ? "Thinking…" : "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionEl.value.trim();
  if (!question) return;

  appendBubble(question, "user");
  questionEl.value = "";
  setBusy(true);

  try {
    const response = await fetch("/v1/support/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, channel: "web" }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    appendBubble(data.reply || "(No reply)", "agent");

    const bits = [];
    if (data.classification_label) bits.push(data.classification_label);
    if (data.outcome) bits.push(`outcome: ${data.outcome}`);
    if (data.action) bits.push(`action: ${data.action}`);
    if (bits.length) appendMeta(bits.join(" · "));
  } catch (err) {
    statusEl.classList.add("error");
    statusEl.textContent =
      "Could not reach the support API. Is the server running?";
    appendBubble(
      "Sorry — I could not reach the support service just now.",
      "agent"
    );
    console.error(err);
  } finally {
    setBusy(false);
    questionEl.focus();
  }
});

questionEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

questionEl.focus();
