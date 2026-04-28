import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { ArrowLeft, Send, AlertCircle } from "lucide-react";

function ts(dt) {
  const d = typeof dt === "string" ? new Date(dt) : dt;
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Chat() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [chat, setChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [crisisActive, setCrisisActive] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    api.getChat(id)
      .then((c) => {
        setChat(c);
        setMessages(c.messages || []);
        if ((c.messages || []).some((m) => m.role === "assistant" && /988/.test(m.content))) {
          setCrisisActive(true);
        }
      })
      .catch(() => navigate("/home"));
  }, [id, navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setSending(true);
    setError(null);
    const optimistic = { role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((m) => [...m, optimistic]);
    setInput("");
    try {
      const resp = await api.sendMessage(id, text);
      setMessages((m) => [...m.slice(0, -1), resp.user_message, resp.assistant_message]);
      if (resp.crisis_detected) setCrisisActive(true);
    } catch (e) {
      if (e?.response?.status === 402) {
        navigate("/pricing");
        return;
      }
      setError("Couldn't send. Please try again.");
      setMessages((m) => m.slice(0, -1));
      setInput(text);
    } finally {
      setSending(false);
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!chat) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-mm">
        <p className="font-serif-mm italic text-mm-secondary mm-pulse">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-mm flex flex-col" data-testid="chat-page">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-[#FDFBF7]/85 backdrop-blur-xl border-b border-[#EBE8E3]">
        <div className="max-w-md mx-auto px-5 py-3.5 flex items-center gap-3">
          <button
            onClick={() => navigate("/home")}
            data-testid="back-button"
            className="p-1.5 -ml-1.5 rounded-full hover:bg-mm-alt"
            aria-label="Back"
          >
            <ArrowLeft size={20} className="text-mm-primary" />
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] uppercase tracking-[0.18em] text-mm-secondary">
              {chat.mode === "manage" ? "Center your mind" : "A listening ear"}
            </p>
            <p className="font-serif-mm text-base text-mm-primary truncate">
              {chat.title}
            </p>
          </div>
        </div>
      </header>

      {/* Crisis banner */}
      {crisisActive && (
        <div
          className="max-w-md w-full mx-auto px-5 pt-4"
          data-testid="crisis-banner"
        >
          <div className="rounded-2xl px-4 py-3 flex gap-3" style={{ background: "#F5EBEB" }}>
            <AlertCircle size={18} className="shrink-0 mt-0.5" style={{ color: "#8C5555" }} />
            <p className="text-sm leading-relaxed" style={{ color: "#8C5555" }}>
              You don&rsquo;t have to go through this alone. Please reach out:
              <br />
              <span className="font-medium">988</span> (US) ·{" "}
              <span className="font-medium">iCall +91 9152987821</span> (India) ·{" "}
              <span className="font-medium">Samaritans 116 123</span> (UK)
            </p>
          </div>
        </div>
      )}

      {/* Messages */}
      <main className="flex-1 max-w-md w-full mx-auto px-5 py-5">
        {messages.length === 0 && (
          <p className="text-center text-mm-secondary italic font-serif-mm text-sm mt-8" data-testid="chat-empty">
            Whenever you&rsquo;re ready.
          </p>
        )}
        <div className="space-y-3">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              data-testid={`message-${m.role}-${i}`}
            >
              <div
                className={`max-w-[85%] px-4 py-3 rounded-2xl text-[15px] leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-mm-brand text-white rounded-br-sm"
                    : "bg-mm-alt text-mm-primary rounded-bl-sm"
                }`}
              >
                {m.content}
                <p
                  className={`text-[10px] mt-1.5 ${
                    m.role === "user" ? "text-white/70" : "text-mm-secondary"
                  }`}
                >
                  {ts(m.created_at)}
                </p>
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start" data-testid="typing-indicator">
              <div className="bg-mm-alt rounded-2xl rounded-bl-sm px-4 py-3">
                <span className="font-serif-mm italic text-mm-secondary mm-pulse text-sm">
                  thinking...
                </span>
              </div>
            </div>
          )}
        </div>
        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <div className="sticky bottom-0 bg-[#FDFBF7]/95 backdrop-blur-xl border-t border-[#EBE8E3]">
        <div className="max-w-md mx-auto px-5 py-3">
          {error && (
            <p className="text-xs text-[#8C5555] mb-2" data-testid="chat-error">{error}</p>
          )}
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder={chat.mode === "manage" ? "What's on your mind?" : "Say it however it comes out..."}
              rows={1}
              className="mm-input resize-none max-h-32"
              data-testid="chat-input"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              data-testid="send-button"
              className="mm-btn-primary !p-3 !rounded-full"
              aria-label="Send"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
