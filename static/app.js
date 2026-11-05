const $ = (id) => document.getElementById(id);
let conversationId = null;

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text; // textContent: never render model output as HTML
  $("messages").appendChild(el);
  $("messages").scrollTop = $("messages").scrollHeight;
}

async function loadConversations() {
  const list = await api("/api/conversations");
  const ul = $("conversations");
  ul.innerHTML = "";
  for (const c of list) {
    const li = document.createElement("li");
    li.className = c.id === conversationId ? "active" : "";
    const title = document.createElement("span");
    title.textContent = c.title;
    const del = document.createElement("button");
    del.textContent = "✕";
    del.title = "Delete";
    del.onclick = async (e) => {
      e.stopPropagation();
      await api(`/api/conversations/${c.id}`, { method: "DELETE" });
      if (conversationId === c.id) newChat();
      loadConversations();
    };
    li.append(title, del);
    li.onclick = () => openConversation(c.id);
    ul.appendChild(li);
  }
}

async function openConversation(id) {
  conversationId = id;
  $("messages").innerHTML = "";
  for (const m of await api(`/api/conversations/${id}/messages`)) addMessage(m.role, m.content);
  loadConversations();
}

function newChat() {
  conversationId = null;
  $("messages").innerHTML = "";
  loadConversations();
}

$("new-chat").onclick = newChat;
$("input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("composer").requestSubmit(); }
});

$("composer").onsubmit = async (e) => {
  e.preventDefault();
  const message = $("input").value.trim();
  if (!message) return;
  $("input").value = "";
  $("send").disabled = true;
  addMessage("user", message);
  try {
    const data = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
    conversationId = data.conversation_id;
    addMessage("assistant", data.reply);
    loadConversations();
  } catch (err) {
    addMessage("error", err.message);
  } finally {
    $("send").disabled = false;
    $("input").focus();
  }
};

api("/api/health").then((h) => ($("provider").textContent = `${h.provider} · ${h.model}`)).catch(() => {});
loadConversations();
