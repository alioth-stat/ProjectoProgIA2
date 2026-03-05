import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import CodeBlock from "./CodeBlock";

function MarkdownContent({ content }) {
  return (
    <ReactMarkdown
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const lang = match ? match[1] : "text";
          if (!inline && match) {
            return (
              <SyntaxHighlighter
                language={lang}
                style={oneDark}
                customStyle={{ borderRadius: "8px", fontSize: "13px" }}
              >
                {String(children).replace(/\n$/, "")}
              </SyntaxHighlighter>
            );
          }
          return (
            <code className="inline-code" {...props}>
              {children}
            </code>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user-row" : "agent-row"}`}>
      <div className={`avatar ${isUser ? "avatar-user" : "avatar-agent"}`}>
        {isUser ? "Tu" : "IA"}
      </div>
      <div className={`bubble ${isUser ? "bubble-user" : "bubble-agent"}`}>
        <div className="bubble-content">
          <MarkdownContent content={message.content} />
        </div>

        {message.patches && message.patches.length > 0 && (
          <div className="patches">
            <p className="patches-title">Cambios sugeridos:</p>
            {message.patches.map((patch, i) => (
              <div key={i} className="patch-item">
                {patch.explanation && (
                  <p className="patch-explanation">{patch.explanation}</p>
                )}
                <CodeBlock
                  code={patch.new_content}
                  language="python"
                  filename={patch.file_path}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
