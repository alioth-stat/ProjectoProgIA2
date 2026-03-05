const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function createSession(sessionId, codeSnippets = []) {
  return request("/api/session", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, code_snippets: codeSnippets }),
  });
}

export async function sendMessage(sessionId, message, codeSnippets = [], activeFile = null) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      message,
      code_snippets: codeSnippets,
      active_file: activeFile,
    }),
  });
}

export async function deleteSession(sessionId) {
  return request(`/api/session/${sessionId}`, { method: "DELETE" });
}
