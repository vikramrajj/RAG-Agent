// llama-chat.js

let recognition;
let isListening = false;
let userProfile = { name: "vikram", device: "Windows", lastApp: null };

window.onload = () => {
  const savedMessages = localStorage.getItem("chatHistory");
  if (savedMessages) document.getElementById("messages").innerHTML = savedMessages;
  switchTab("messages");
};

function switchTab(tabId) {
  document.querySelectorAll(".tab").forEach(tab => tab.classList.remove("active"));
  document.querySelectorAll("#messages, #history").forEach(div => div.style.display = "none");
  document.querySelector(`.tab[onclick*="${tabId}"]`).classList.add("active");
  document.getElementById(tabId).style.display = "block";
}

function inferAppFromInput(text) {
  const lower = text.toLowerCase();
  if (lower.includes("teams")) return "Teams";
  if (lower.includes("excel")) return "Excel";
  return "Outlook";
}

async function sendMessage(inputOverride = null) {
  const inputField = document.getElementById("user-input");
  const input = inputOverride || inputField.value.trim();
  if (!input) return;

  const inferredApp = inferAppFromInput(input);
  userProfile.lastApp = inferredApp;
  appendMessage("You", input);
  inputField.value = "";

  const systemPrompt = `You are a diagnostic assistant helping ${userProfile.name} troubleshoot ${inferredApp} on ${userProfile.device}. Ask clarifying questions before suggesting fixes. Offer to open the web version and run diagnostics.`;
  const fullPrompt = `${systemPrompt}\nUser: ${input}`;

  try {
    const response = await fetch("http://localhost:11434/api/generate", {
      method: "POST",
      body: JSON.stringify({ model: "llama2", prompt: fullPrompt, stream: false }),
      headers: { "Content-Type": "application/json" }
    });

    const data = await response.json();
    appendMessage("Assistant", data.response);

    const lowerInput = input.toLowerCase();
    if (lowerInput.includes("stop") || lowerInput.includes("stop listening")) {
      stopVoiceInput();
      appendMessage("Assistant", "Voice input stopped by command.");
      return;
    }

    const triggerWords = ["outlook", "email", "teams", "excel", "crash", "not responding"];
    const matched = triggerWords.some(word => lowerInput.includes(word));

    if (matched) {
      const confirmAction = confirm(`Run diagnostics and open web version for ${inferredApp} in a new tab?`);
      if (!confirmAction) {
        appendMessage("Assistant", "Action cancelled.");
        return;
      }

      let url = "";
      if (inferredApp === "Outlook") url = "https://outlook.office.com/mail/";
      if (inferredApp === "Teams") url = "https://teams.microsoft.com/";
      if (inferredApp === "Excel") url = "https://office.live.com/start/Excel.aspx";

      // Open in a new tab
      if (url) {
        const newTab = window.open(url, "_blank");
        if (!newTab || newTab.closed || typeof newTab.closed === 'undefined') {
          appendMessage("Assistant", "New tab blocked by browser. Please allow popups for this site and try again.");
        } else {
          appendMessage("Assistant", `Opened ${inferredApp} web version in a new tab. Continuing troubleshooting...`);
        }
      }

      // Placeholder for diagnostics (update endpoint logic as needed)
      appendMessage("Assistant", `Running diagnostics for ${inferredApp}... (Note: Diagnostics endpoint not fully implemented yet)`);
    }
  } catch (error) {
    console.error("Error:", error);
    appendMessage("Assistant", "Error communicating with server. Please try again.");
  }
}

function appendMessage(sender, text) {
  const timestamp = `<span class="timestamp">${getTimestamp()}</span>`;
  const msg = document.createElement("div");
  msg.innerHTML = `<strong>${sender}:</strong> ${text} ${timestamp}`;
  const messagesDiv = document.getElementById("messages");
  messagesDiv.appendChild(msg);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  localStorage.setItem("chatHistory", messagesDiv.innerHTML);
}

function getTimestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micStatus = document.getElementById("mic-status");

  if (!SpeechRecognition) {
    alert("Voice input not supported in this browser.");
    return;
  }

  if (isListening) {
    stopVoiceInput();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.continuous = true;

  recognition.onstart = () => {
    micStatus.textContent = "🎙️ Listening...";
    micStatus.classList.add("blinking");
    isListening = true;
  };

  recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();

    if (transcript === "stop" || transcript === "stop listening") {
      stopVoiceInput();
      appendMessage("Assistant", "Voice input stopped by command.");
      return;
    }

    document.getElementById("user-input").value = transcript;
    sendMessage(transcript);
  };

  recognition.onerror = (event) => {
    console.error("🎤 Voice input error:", event.error);
    alert("Voice input failed. Please check microphone permissions.");
    stopVoiceInput();
  };

  recognition.onend = () => {
    stopVoiceInput();
  };

  recognition.start();
}

function stopVoiceInput() {
  if (recognition) recognition.stop();
  const micStatus = document.getElementById("mic-status");
  micStatus.textContent = "";
  micStatus.classList.remove("blinking");
  isListening = false;
}

function exportHistory() {
  const historyContent = document.getElementById("history").innerText;
  const blob = new Blob([historyContent], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `diagnostics_${userProfile.name}_${getTimestamp().replace(/:/g, '-')}.txt`;
  link.click();
}

function levenshteinDistance(a, b) {
  const matrix = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
  for (let j = 0; j <= b.length; j++) matrix[0][j] = j;

  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,
        matrix[i][j - 1] + 1,
        matrix[i - 1][j - 1] + cost
      );
    }
  }
  return matrix[a.length][b.length];
}