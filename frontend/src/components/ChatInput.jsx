import { useState, useRef } from "react";

const SUGGESTIONS = [
  "Explica como funciona este codigo",
  "Genera una funcion que ordene una lista",
  "Refactoriza el codigo para que sea mas legible",
  "Escribe tests para este modulo",
  "Analiza el codigo y encuentra errores",
  "Genera docstrings para todas las funciones",
];

export default function ChatInput({ onSend, loading }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setText("");
    textareaRef.current?.focus();
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="chat-input-area">
      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className="suggestion-chip"
            onClick={() => { setText(s); textareaRef.current?.focus(); }}
            disabled={loading}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="input-row">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu tarea o pregunta... (Enter para enviar)"
          rows={2}
          disabled={loading}
        />
        <button
          className={`send-btn ${loading ? "loading" : ""}`}
          onClick={submit}
          disabled={loading || !text.trim()}
        >
          {loading ? "..." : "Enviar"}
        </button>
      </div>
    </div>
  );
}
