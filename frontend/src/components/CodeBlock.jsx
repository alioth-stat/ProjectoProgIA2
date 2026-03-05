import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useState } from "react";

export default function CodeBlock({ code, language = "python", filename }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-lang">{filename || language}</span>
        <button className="copy-btn" onClick={copy}>
          {copied ? "Copiado!" : "Copiar"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        customStyle={{ margin: 0, borderRadius: "0 0 8px 8px", fontSize: "13px" }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
