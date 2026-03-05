import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { sendMessage, createSession } from "../api/agent";

export function useSession() {
  const sessionId = useRef(uuidv4());
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const addMessage = (role, content, patches = []) => {
    setMessages((prev) => [
      ...prev,
      { id: uuidv4(), role, content, patches, ts: Date.now() },
    ]);
  };

  const send = useCallback(async (text, snippets = [], activeFile = null) => {
    if (!text.trim()) return;
    setError(null);
    addMessage("user", text);
    setLoading(true);
    try {
      const res = await sendMessage(sessionId.current, text, snippets, activeFile);
      addMessage("agent", res.message, res.patches || []);
    } catch (e) {
      setError(e.message);
      addMessage("agent", `Error: ${e.message}`, []);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSnippets = useCallback(async (snippets) => {
    setError(null);
    try {
      await createSession(sessionId.current, snippets);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const clearChat = useCallback(() => {
    sessionId.current = uuidv4();
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, send, loadSnippets, clearChat };
}
