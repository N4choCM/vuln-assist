import { useCallback, useState } from "react";
import { DialogueApiError, sendMessage } from "./api/dialogue";
import { ChatInput } from "./components/ChatInput";
import { ChatWindow } from "./components/ChatWindow";
import { IconNewChat } from "./components/Icons";
import type { ChatMessage } from "./types/dialogue";
import "./styles/app.css";

const TAGLINE = "Talk CVEs. Skip the manual search.";

const EXAMPLE_QUERIES = [
  "What is CVE-2021-44228?",
  "Show critical vulnerabilities in Apache",
  "find product",
] as const;

function createId(): string {
  return crypto.randomUUID();
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = useCallback(
    async (text: string) => {
      setError(null);
      setMessages((prev) => [
        ...prev,
        { id: createId(), role: "user", text },
      ]);
      setLoading(true);

      try {
        const response = await sendMessage(text, sessionId);
        setSessionId(response.session_id);
        setMessages((prev) => [
          ...prev,
          {
            id: createId(),
            role: "assistant",
            text: response.reply,
            meta: response,
          },
        ]);
      } catch (err) {
        const message =
          err instanceof DialogueApiError
            ? err.message
            : "Something went wrong. Please try again.";
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId],
  );

  const handleNewChat = () => {
    setSessionId(null);
    setMessages([]);
    setError(null);
  };

  const showWelcome = messages.length === 0 && !loading;

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__brand">
          <img
            src="/vulnassist-logo.png"
            alt=""
            className="app-header__logo"
            width={40}
            height={40}
          />
          <div>
            <h1 className="app-header__title">VulnAssist</h1>
            <p className="app-header__subtitle">{TAGLINE}</p>
          </div>
        </div>
        <button
          type="button"
          className="app-header__new-chat"
          onClick={handleNewChat}
          disabled={loading}
          aria-label="New chat"
          title="New chat"
        >
          <IconNewChat size={20} />
        </button>
      </header>

      <main className="app-main">
        {showWelcome && (
          <section className="welcome">
            <p>
              Ask about CVE identifiers, CVSS scores, products, or severity
              filters in natural language.
            </p>
            <ul className="welcome__examples">
              {EXAMPLE_QUERIES.map((query) => (
                <li key={query}>
                  <button
                    type="button"
                    className="welcome__example-btn"
                    onClick={() => handleSend(query)}
                    disabled={loading}
                  >
                    {query}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}

        <ChatWindow
          messages={messages}
          loading={loading}
          showTechnicalDetails={showTechnicalDetails}
        />

        {error && (
          <p className="app-error" role="alert">
            {error}
          </p>
        )}
      </main>

      <footer className="app-footer">
        <label className="app-footer__toggle">
          <input
            type="checkbox"
            checked={showTechnicalDetails}
            onChange={(e) => setShowTechnicalDetails(e.target.checked)}
          />
          Show technical details
        </label>
        <ChatInput disabled={loading} onSend={handleSend} />
      </footer>
    </div>
  );
}
