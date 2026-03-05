import { useState } from "react";

const DEFAULT_SNIPPET = {
  filename: "mi_codigo.py",
  content: "",
  language: "python",
};

export default function CodePanel({ onLoad }) {
  const [snippets, setSnippets] = useState([{ ...DEFAULT_SNIPPET }]);
  const [status, setStatus] = useState(null);

  const updateSnippet = (index, field, value) => {
    setSnippets((prev) =>
      prev.map((s, i) => (i === index ? { ...s, [field]: value } : s))
    );
  };

  const addSnippet = () => {
    setSnippets((prev) => [...prev, { ...DEFAULT_SNIPPET, filename: `archivo_${prev.length + 1}.py` }]);
  };

  const removeSnippet = (index) => {
    setSnippets((prev) => prev.filter((_, i) => i !== index));
  };

  const handleLoad = async () => {
    const filled = snippets.filter((s) => s.content.trim());
    if (!filled.length) return;
    setStatus("Cargando...");
    try {
      await onLoad(filled);
      setStatus(`${filled.length} archivo(s) cargado(s).`);
    } catch {
      setStatus("Error al cargar.");
    }
    setTimeout(() => setStatus(null), 3000);
  };

  return (
    <aside className="code-panel">
      <div className="code-panel-header">
        <span className="panel-title">Codigo de contexto</span>
        <button className="btn-secondary" onClick={addSnippet}>+ Archivo</button>
      </div>

      <div className="snippets-list">
        {snippets.map((s, i) => (
          <div key={i} className="snippet-item">
            <div className="snippet-row">
              <input
                className="filename-input"
                value={s.filename}
                onChange={(e) => updateSnippet(i, "filename", e.target.value)}
                placeholder="nombre_archivo.py"
              />
              <select
                className="lang-select"
                value={s.language}
                onChange={(e) => updateSnippet(i, "language", e.target.value)}
              >
                {["python", "javascript", "typescript", "java", "go", "rust"].map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
              {snippets.length > 1 && (
                <button className="btn-remove" onClick={() => removeSnippet(i)}>✕</button>
              )}
            </div>
            <textarea
              className="code-textarea"
              value={s.content}
              onChange={(e) => updateSnippet(i, "content", e.target.value)}
              placeholder="Pega tu codigo aqui..."
              rows={8}
              spellCheck={false}
            />
          </div>
        ))}
      </div>

      <div className="panel-footer">
        {status && <span className="status-text">{status}</span>}
        <button className="btn-primary" onClick={handleLoad}>
          Cargar contexto
        </button>
      </div>
    </aside>
  );
}
