
"use client";

import { useState, useRef, useEffect } from "react";

// const API_URL = "http://localhost:5000/api/chat";
const API_URL = "https://fd-advisor-ai-chatbot-1.onrender.com/api/chat";

type Message = {
  role: "user" | "assistant";
  content: string;
  topics?: string[];
  timestamp: string; // store as string to avoid hydration mismatch
};

const suggestions = [
  "I earn $2000/month. How do I budget?",
  "What is compound interest?",
  "Should I invest or pay off debt first?",
  "Explain ETFs like I'm a beginner",
  "How do I build an emergency fund?",
  "Is crypto a good investment?",
];

const getTime = () =>
  new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: true });

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome! I'm your personal Financial AI Advisor. Whether you're just starting out or planning your next big move — ask me anything about money, investing, savings, loans, or budgeting. I speak your language. 💰",
      timestamp: "",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [convId] = useState(() => `session_${Math.random().toString(36).slice(2)}`);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    const userMessage: Message = {
      role: "user",
      content: msg,
      timestamp: getTime(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, conversation_id: convId }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response || "I couldn't process that. Please try again.",
          topics: data.topics || [],
          timestamp: getTime(),
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠️ Could not reach the server. Make sure your backend is running at localhost:5000.",
          timestamp: getTime(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      <style>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
          --bg: #0d0f0e;
          --surface: #151918;
          --surface2: #1c211f;
          --border: #2a312e;
          --gold: #c9a84c;
          --gold-dim: #a8843a;
          --gold-glow: rgba(201,168,76,0.15);
          --green: #4caf7d;
          --green-dim: #3a8a60;
          --text: #e8e4dc;
          --muted: #8a9490;
          --user-bg: #1a2420;
          --ai-bg: #161b19;
          --font-display: 'Playfair Display', Georgia, serif;
          --font-body: 'DM Sans', sans-serif;
          --radius: 16px;
          --radius-sm: 10px;
        }

        body {
          background: var(--bg);
          color: var(--text);
          font-family: var(--font-body);
          height: 100dvh;
          overflow: hidden;
        }

        .app {
          display: flex;
          flex-direction: column;
          height: 100dvh;
          max-width: 860px;
          margin: 0 auto;
          padding: 0 16px;
        }

        /* ── Header ── */
        .header {
          padding: 20px 0 16px;
          border-bottom: 1px solid var(--border);
          display: flex;
          align-items: center;
          gap: 14px;
          flex-shrink: 0;
        }

        .logo {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--gold), var(--gold-dim));
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          flex-shrink: 0;
          box-shadow: 0 0 20px var(--gold-glow);
        }

        .header-text h1 {
          font-family: var(--font-display);
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--gold);
          letter-spacing: 0.01em;
        }

        .header-text p {
          font-size: 0.75rem;
          color: var(--muted);
          font-weight: 300;
          margin-top: 1px;
        }

        .status {
          margin-left: auto;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.72rem;
          color: var(--green);
          font-weight: 500;
        }

        .status-dot {
          width: 7px;
          height: 7px;
          background: var(--green);
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }

        /* ── Messages ── */
        .messages {
          flex: 1;
          overflow-y: auto;
          padding: 20px 0;
          display: flex;
          flex-direction: column;
          gap: 20px;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }

        .messages::-webkit-scrollbar { width: 4px; }
        .messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        /* ── Suggestions ── */
        .suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 4px 0 8px;
          animation: fadeUp 0.5s ease both;
        }

        .suggestion-label {
          width: 100%;
          font-size: 0.7rem;
          color: var(--muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 500;
          margin-bottom: 2px;
        }

        .suggestion-btn {
          background: var(--surface2);
          border: 1px solid var(--border);
          color: var(--text);
          font-family: var(--font-body);
          font-size: 0.78rem;
          padding: 7px 13px;
          border-radius: 20px;
          cursor: pointer;
          transition: all 0.2s;
          font-weight: 400;
        }

        .suggestion-btn:hover {
          border-color: var(--gold-dim);
          color: var(--gold);
          background: var(--gold-glow);
        }

        /* ── Message bubble ── */
        .msg-row {
          display: flex;
          gap: 12px;
          animation: fadeUp 0.35s ease both;
        }

        .msg-row.user { flex-direction: row-reverse; }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .avatar {
          width: 34px;
          height: 34px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 16px;
          flex-shrink: 0;
          margin-top: 2px;
        }

        .avatar.ai {
          background: linear-gradient(135deg, var(--gold), var(--gold-dim));
          box-shadow: 0 0 12px var(--gold-glow);
        }

        .avatar.user {
          background: var(--surface2);
          border: 1px solid var(--border);
        }

        .bubble-wrap { display: flex; flex-direction: column; gap: 4px; max-width: 78%; }
        .msg-row.user .bubble-wrap { align-items: flex-end; }

        .bubble {
          padding: 13px 16px;
          border-radius: var(--radius);
          font-size: 0.9rem;
          line-height: 1.65;
          white-space: pre-wrap;
          word-break: break-word;
        }

        .bubble.ai {
          background: var(--ai-bg);
          border: 1px solid var(--border);
          border-top-left-radius: 4px;
          color: var(--text);
        }

        .bubble.user {
          background: var(--user-bg);
          border: 1px solid #2d3d36;
          border-top-right-radius: 4px;
          color: var(--text);
        }

        .meta {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 0 2px;
        }

        .time {
          font-size: 0.68rem;
          color: var(--muted);
        }

        .topics {
          display: flex;
          gap: 5px;
          flex-wrap: wrap;
        }

        .topic-tag {
          font-size: 0.65rem;
          padding: 2px 8px;
          border-radius: 10px;
          background: var(--gold-glow);
          border: 1px solid rgba(201,168,76,0.25);
          color: var(--gold-dim);
          font-weight: 500;
          text-transform: capitalize;
        }

        /* ── Typing indicator ── */
        .typing-row {
          display: flex;
          gap: 12px;
          animation: fadeUp 0.3s ease both;
        }

        .typing-bubble {
          background: var(--ai-bg);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          border-top-left-radius: 4px;
          padding: 14px 18px;
          display: flex;
          gap: 5px;
          align-items: center;
        }

        .dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--gold-dim);
          animation: bounce 1.2s infinite;
        }

        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40%            { transform: translateY(-6px); opacity: 1; }
        }

        /* ── Input area ── */
        .input-area {
          padding: 14px 0 20px;
          border-top: 1px solid var(--border);
          flex-shrink: 0;
        }

        .input-box {
          display: flex;
          align-items: flex-end;
          gap: 10px;
          background: var(--surface2);
          border: 1px solid var(--border);
          border-radius: var(--radius);
          padding: 10px 12px;
          transition: border-color 0.2s;
        }

        .input-box:focus-within {
          border-color: var(--gold-dim);
          box-shadow: 0 0 0 3px var(--gold-glow);
        }

        textarea {
          flex: 1;
          background: transparent;
          border: none;
          outline: none;
          color: var(--text);
          font-family: var(--font-body);
          font-size: 0.9rem;
          line-height: 1.5;
          resize: none;
          max-height: 120px;
          min-height: 24px;
          padding: 2px 0;
        }

        textarea::placeholder { color: var(--muted); }

        .send-btn {
          width: 38px;
          height: 38px;
          border-radius: 10px;
          background: linear-gradient(135deg, var(--gold), var(--gold-dim));
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: all 0.2s;
          box-shadow: 0 0 12px var(--gold-glow);
        }

        .send-btn:hover:not(:disabled) {
          transform: scale(1.06);
          box-shadow: 0 0 20px rgba(201,168,76,0.35);
        }

        .send-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .send-btn svg { color: #0d0f0e; }

        .hint {
          text-align: center;
          font-size: 0.68rem;
          color: var(--muted);
          margin-top: 10px;
        }

        /* ── Divider disclaimer ── */
        .disclaimer-bubble {
          font-size: 0.78rem;
          color: var(--muted);
          font-style: italic;
          line-height: 1.6;
        }

        .disclaimer-bubble em {
          color: rgba(201,168,76,0.7);
          font-style: normal;
        }
      `}</style>

      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="logo">💰</div>
          <div className="header-text">
            <h1>FinanceAI Advisor</h1>
            <p>Powered by Groq · LangGraph · Llama 3.3</p>
          </div>
          <div className="status">
            <div className="status-dot" />
            Online
          </div>
        </header>

        {/* Messages */}
        <div className="messages">
          {/* Suggestions shown only at start */}
          {messages.length === 1 && (
            <div className="suggestions">
              <span className="suggestion-label">Try asking</span>
              {suggestions.map((s) => (
                <button
                  key={s}
                  className="suggestion-btn"
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`msg-row ${msg.role}`}>
              <div className={`avatar ${msg.role === "assistant" ? "ai" : "user"}`}>
                {msg.role === "assistant" ? "💼" : "👤"}
              </div>
              <div className="bubble-wrap">
                <div className={`bubble ${msg.role === "assistant" ? "ai" : "user"}`}>
                  {msg.content}
                </div>
                <div className="meta">
                  {mounted && msg.timestamp && (
                    <span className="time">{msg.timestamp}</span>
                  )}
                  {msg.topics && msg.topics.length > 0 && (
                    <div className="topics">
                      {msg.topics.map((t) => (
                        <span key={t} className="topic-tag">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div className="typing-row">
              <div className="avatar ai">💼</div>
              <div className="typing-bubble">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-box">
            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="Ask me anything about money, investing, savings..."
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
              }}
              onKeyDown={handleKey}
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <p className="hint">Press Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </>
  );
}
