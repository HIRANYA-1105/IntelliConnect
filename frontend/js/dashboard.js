// IntelliConnect — dashboard, now talking to the real Flask backend
// (see backend/app.py — POST /api/chat runs the full NLU + escalation +
// network + billing + recommendation pipeline for every message)

const API_BASE = "https://intelliconnect.onrender.com";
const SESSION_KEY = "ic_user";

const sessionRaw = localStorage.getItem(SESSION_KEY);
if (!sessionRaw) window.location.href = "index.html";
const currentUser = JSON.parse(sessionRaw);

document.getElementById("userName").textContent = currentUser.name;
document.getElementById("userPlan").textContent = currentUser.plan || "No plan on file";
document.getElementById("userAvatar").textContent = (currentUser.name || "G").trim()[0].toUpperCase();

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem(SESSION_KEY);
  window.location.href = "index.html";
});

function nowLabel() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function newThreadId() {
  return (crypto.randomUUID ? crypto.randomUUID() : "t-" + Date.now() + "-" + Math.random().toString(36).slice(2));
}

// ---- state ----
let threads = [{ id: newThreadId(), title: "New conversation", risk: 8 }];
let activeThreadId = threads[0].id;
let messages = {
  [activeThreadId]: [{ role: "bot", text: `Hi ${currentUser.name.split(" ")[0] || "there"}, I'm the IntelliConnect assistant. Tell me what's going on and I'll take it from here.`, time: nowLabel() }],
};
const lastAnalysisByThread = {};

// ---- DOM refs ----
const threadListEl = document.getElementById("threadList");
const messagesEl = document.getElementById("messages");
const intentTag = document.getElementById("intentTag");
const confidenceBar = document.getElementById("confidenceBar");
const confidenceLabel = document.getElementById("confidenceLabel");
const riskMarker = document.getElementById("riskMarker");
const riskLabel = document.getElementById("riskLabel");
const actionCard = document.getElementById("actionCard");
const escalateBtn = document.getElementById("escalateBtn");
const composerInput = document.getElementById("composerInput");

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showTypingIndicator() {
  const el = document.createElement("div");
  el.className = "msg bot typing";
  el.id = "typingIndicator";
  el.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function renderThreads() {
  threadListEl.innerHTML = "";
  threads.forEach((t) => {
    const el = document.createElement("div");
    el.className = "thread-item" + (t.id === activeThreadId ? " active" : "");
    el.tabIndex = 0;
    el.innerHTML = `<span>${escapeHtml(t.title)}</span><span class="thread-tag${t.risk >= 55 ? " risk" : ""}"></span>`;
    el.addEventListener("click", () => {
      activeThreadId = t.id;
      renderThreads();
      renderMessages();
      renderInsight(lastAnalysis(t.id));
    });
    threadListEl.appendChild(el);
  });
}

function renderMessages() {
  const list = messages[activeThreadId] || [];
  messagesEl.innerHTML = "";
  list.forEach((m) => {
    const el = document.createElement("div");
    el.className = "msg " + m.role;
    el.innerHTML = `${escapeHtml(m.text)}<span class="meta">${m.time}</span>`;
    messagesEl.appendChild(el);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function lastAnalysis(threadId) {
  return lastAnalysisByThread[threadId] || { intentLabel: "Awaiting message…", confidence: 0, risk: 8 };
}

function renderInsight({ intentLabel, confidence, risk }) {
  intentTag.textContent = intentLabel;
  confidenceBar.style.width = confidence + "%";
  confidenceLabel.textContent = Math.round(confidence) + "%";
  riskMarker.style.left = risk + "%";

  riskLabel.classList.remove("low", "medium", "high");
  if (risk >= 70) {
    riskLabel.classList.add("high");
    riskLabel.textContent = "High — likely to escalate";
    actionCard.innerHTML = "<strong>Recommended action</strong>Route to a human agent. Sentiment and repeated contact suggest self-service won't resolve this.";
    escalateBtn.disabled = false;
  } else if (risk >= 40) {
    riskLabel.classList.add("medium");
    riskLabel.textContent = "Medium — keep monitoring";
    actionCard.innerHTML = "<strong>Recommended action</strong>Continue with guided troubleshooting, but prepare a handoff if the next reply shows more frustration.";
    escalateBtn.disabled = false;
  } else {
    riskLabel.classList.add("low");
    riskLabel.textContent = "Low — model is monitoring";
    actionCard.innerHTML = "<strong>Recommended action</strong>No action needed. Continue the automated flow.";
    escalateBtn.disabled = true;
  }
}

// ---- new conversation ----
document.getElementById("newChatBtn").addEventListener("click", () => {
  const id = newThreadId();
  threads.push({ id, title: "New conversation", risk: 8 });
  messages[id] = [{ role: "bot", text: "New conversation started. What can I help with?", time: nowLabel() }];
  activeThreadId = id;
  renderThreads();
  renderMessages();
  renderInsight(lastAnalysis(id));
});

// ---- send message: calls the real backend ----
document.getElementById("composerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = composerInput.value.trim();
  if (!text) return;

  messages[activeThreadId].push({ role: "user", text, time: nowLabel() });
  const thread = threads.find((t) => t.id === activeThreadId);
  if (thread.title === "New conversation") {
    thread.title = text.length > 26 ? text.slice(0, 26) + "…" : text;
  }
  renderThreads();
  renderMessages();

  composerInput.value = "";
  composerInput.disabled = true;
  showTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUser.id, thread_id: activeThreadId, message: text }),
    });
    const data = await res.json();

    hideTypingIndicator();

    if (!res.ok) {
      messages[activeThreadId].push({ role: "bot", text: "Error: " + (data.error || "something went wrong on the server."), time: nowLabel() });
      renderMessages();
      return;
    }

    thread.risk = data.risk_score;
    lastAnalysisByThread[activeThreadId] = {
      intentLabel: data.intent_label,
      confidence: data.confidence,
      risk: data.risk_score,
    };

    messages[activeThreadId].push({ role: "bot", text: data.reply, time: nowLabel() });

    renderThreads();
    renderMessages();
    renderInsight(lastAnalysisByThread[activeThreadId]);

  } catch (err) {
    hideTypingIndicator();
    messages[activeThreadId].push({
      role: "bot",
      text: `Can't reach the backend at ${API_BASE}. Make sure "python app.py" is running in the intelliconnect-backend folder, then send your message again.`,
      time: nowLabel(),
    });
    renderMessages();
  } finally {
    composerInput.disabled = false;
    composerInput.focus();
  }
});

escalateBtn.addEventListener("click", () => {
  messages[activeThreadId].push({ role: "bot", text: "Connecting you to a human specialist now — they'll have full context from this chat.", time: nowLabel() });
  renderMessages();
  escalateBtn.disabled = true;
  escalateBtn.textContent = "Escalated ✓";
});

// ---- voice input: record -> send to backend -> fill the composer ----
const micBtn = document.getElementById("micBtn");
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
      await sendForTranscription(audioBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    micBtn.classList.add("recording");
    micBtn.textContent = "⏹";
  } catch (err) {
    messages[activeThreadId].push({
      role: "bot",
      text: "Couldn't access your microphone — please check browser permissions and try again.",
      time: nowLabel(),
    });
    renderMessages();
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    micBtn.classList.remove("recording");
    micBtn.textContent = "🎤";
  }
}

async function sendForTranscription(audioBlob) {
  composerInput.disabled = true;
  composerInput.placeholder = "Transcribing your voice message…";

  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "voice-message.webm");

    const res = await fetch(`${API_BASE}/api/voice/transcribe`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (data.success && data.text) {
      composerInput.value = data.text;
    } else {
      messages[activeThreadId].push({
        role: "bot",
        text: data.error || "Couldn't transcribe that — please try again or type your issue.",
        time: nowLabel(),
      });
      renderMessages();
    }
  } catch (err) {
    messages[activeThreadId].push({
      role: "bot",
      text: `Can't reach the voice service at ${API_BASE}. Make sure the backend is running.`,
      time: nowLabel(),
    });
    renderMessages();
  } finally {
    composerInput.disabled = false;
    composerInput.placeholder = "Describe your issue — e.g. 'My internet has been down since morning'";
    composerInput.focus();
  }
}

micBtn.addEventListener("click", () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// initial paint
renderThreads();
renderMessages();
renderInsight(lastAnalysis(activeThreadId));
