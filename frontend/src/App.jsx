import { useEffect, useRef } from "react";
import { useSession } from "./hooks/useSession";
import MessageBubble from "./components/MessageBubble";
import ChatInput from "./components/ChatInput";
import CodePanel from "./components/CodePanel";
import "./App.css";

export default function App() {
  const { messages, loading, error, send, loadSnippets, clearChat } = useSession();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <span className="logo">&#123;&#125;</span>
          <h1 className="app-title">Agente IA de Programacion</h1>
        </div>
        <button className="btn-clear" onClick={clearChat}>Nueva sesion</button>
      </header>

      <div className="main-layout">
        {/* Left: Code context panel */}
        <CodePanel onLoad={loadSnippets} />

        {/* Right: Chat */}
        <div className="chat-section">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="empty-state">
                <p className="empty-icon">&#129302;</p>
                <p className="empty-title">Listo para ayudarte con tu codigo</p>
                <p className="empty-hint">
                  Pega tu codigo en el panel izquierdo, luego escribe tu tarea.
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {loading && (
              <div className="message-row agent-row">
                <div className="avatar avatar-agent">IA</div>
                <div className="bubble bubble-agent">
                  <div className="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="error-banner">{error}</div>
            )}

            <div ref={bottomRef} />
          </div>

          <ChatInput onSend={send} loading={loading} />
        </div>
      </div>
    </div>
  );
}
