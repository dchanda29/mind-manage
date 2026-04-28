import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Brain, Ear, LogOut, Sparkles, Trash2, ArrowRight, Lock } from "lucide-react";

function formatRelative(dt) {
  if (!dt) return "";
  const d = typeof dt === "string" ? new Date(dt) : dt;
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Home() {
  const { user, logout } = useAuth();
  const [quote, setQuote] = useState(null);
  const [chats, setChats] = useState([]);
  const [sub, setSub] = useState(null);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    api.getWelcomeQuote().then(setQuote).catch(() => {});
    refreshChats();
    api.getSubStatus().then(setSub).catch(() => {});
  }, []);

  const refreshChats = () => {
    api.listChats().then(setChats).catch(() => setChats([]));
  };

  const trialMsLeft = (() => {
    if (!sub?.until) return null;
    return new Date(sub.until).getTime() - Date.now();
  })();
  const trialDaysLeft = trialMsLeft ? Math.max(0, Math.ceil(trialMsLeft / 86400000)) : null;

  const handleStartChat = async (mode) => {
    if (!sub?.has_access) {
      navigate("/pricing");
      return;
    }
    if (creating) return;
    setCreating(true);
    try {
      const chat = await api.createChat(mode);
      navigate(`/chat/${chat.chat_id}`);
    } catch (e) {
      if (e?.response?.status === 402) navigate("/pricing");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    e.preventDefault();
    await api.deleteChat(id).catch(() => {});
    refreshChats();
  };

  return (
    <div className="min-h-screen bg-mm">
      <div className="max-w-md mx-auto px-6 py-8">
        {/* Header */}
        <header className="flex items-center justify-between mb-8 mm-fadein" data-testid="home-header">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-mm-secondary">
              MindManage
            </p>
            <h1 className="font-serif-mm text-2xl mt-1 text-mm-primary" data-testid="greeting">
              Hi, {user?.name?.split(" ")[0] || "friend"}.
            </h1>
          </div>
          <button
            onClick={async () => { await logout(); navigate("/"); }}
            data-testid="logout-button"
            className="p-2.5 rounded-full bg-mm-alt hover:bg-[#ebe8e3] transition-colors"
            aria-label="Logout"
          >
            <LogOut size={18} className="text-mm-secondary" />
          </button>
        </header>

        {/* Subscription state */}
        {sub && (
          <div
            className={`mm-card px-5 py-3 mb-6 flex items-center justify-between mm-fadein ${
              !sub.has_access ? "border-[#A35858]/30" : ""
            }`}
            data-testid="sub-status"
          >
            <div className="flex items-center gap-2.5">
              {sub.has_access ? (
                <Sparkles size={16} className="text-mm-brand" />
              ) : (
                <Lock size={16} className="text-[#8C5555]" />
              )}
              <p className="text-sm text-mm-primary">
                {sub.state === "trial" && (
                  <>
                    Free trial · <span className="font-medium">{trialDaysLeft}d left</span>
                  </>
                )}
                {sub.state === "active" && (
                  <>Subscribed · <span className="capitalize font-medium">{sub.plan}</span></>
                )}
                {sub.state === "expired" && <>Trial ended</>}
              </p>
            </div>
            {!sub.has_access || sub.state === "trial" ? (
              <button
                onClick={() => navigate("/pricing")}
                data-testid="upgrade-link"
                className="text-xs uppercase tracking-[0.15em] text-mm-brand hover:underline"
              >
                {sub.has_access ? "Upgrade" : "Continue"}
              </button>
            ) : null}
          </div>
        )}

        {/* Quote */}
        {quote && (
          <blockquote className="mb-9 mm-fadein" data-testid="quote-card">
            <p className="font-serif-mm italic text-xl leading-snug text-mm-primary">
              &ldquo;{quote.text}&rdquo;
            </p>
            <p className="mt-2 text-xs uppercase tracking-[0.18em] text-mm-secondary">
              — {quote.author}
            </p>
          </blockquote>
        )}

        {/* Mode picker */}
        <h2 className="font-serif-mm text-lg text-mm-primary mb-3">
          What do you need today?
        </h2>
        <div className="grid grid-cols-1 gap-4 mb-10 mm-stagger">
          <button
            onClick={() => handleStartChat("manage")}
            data-testid="mode-manage-button"
            disabled={creating}
            className="text-left mm-card p-6 hover:shadow-[0_8px_30px_rgba(45,40,42,0.08)] transition-shadow group disabled:opacity-60"
          >
            <div className="flex items-start justify-between">
              <Brain size={28} className="text-mm-brand" strokeWidth={1.5} />
              <ArrowRight size={18} className="text-mm-secondary group-hover:translate-x-1 transition-transform" />
            </div>
            <h3 className="font-serif-mm text-2xl mt-5 text-mm-primary">
              Center your mind
            </h3>
            <p className="text-sm text-mm-secondary mt-1.5 leading-relaxed">
              Tame intrusive thoughts, refocus, breathe. Practical tools.
            </p>
          </button>

          <button
            onClick={() => handleStartChat("support")}
            data-testid="mode-support-button"
            disabled={creating}
            className="text-left mm-card p-6 hover:shadow-[0_8px_30px_rgba(45,40,42,0.08)] transition-shadow group disabled:opacity-60"
            style={{ background: "#F4F1ED" }}
          >
            <div className="flex items-start justify-between">
              <Ear size={28} className="text-mm-brand" strokeWidth={1.5} />
              <ArrowRight size={18} className="text-mm-secondary group-hover:translate-x-1 transition-transform" />
            </div>
            <h3 className="font-serif-mm text-2xl mt-5 text-mm-primary">
              A listening ear
            </h3>
            <p className="text-sm text-mm-secondary mt-1.5 leading-relaxed">
              Just say it out. No advice unless you ask. We&rsquo;re here.
            </p>
          </button>
        </div>

        {/* Recent chats */}
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-serif-mm text-lg text-mm-primary">Recent</h2>
          <p className="text-xs text-mm-secondary">
            {chats.length}/5 saved
          </p>
        </div>

        {chats.length === 0 ? (
          <p className="text-sm text-mm-secondary italic" data-testid="empty-chats">
            No chats yet — start above when you&rsquo;re ready.
          </p>
        ) : (
          <ul className="divide-y divide-[#EBE8E3]" data-testid="chats-list">
            {chats.map((c) => (
              <li
                key={c.chat_id}
                onClick={() => navigate(`/chat/${c.chat_id}`)}
                className="py-3.5 flex items-center justify-between cursor-pointer group"
                data-testid={`chat-item-${c.chat_id}`}
              >
                <div className="min-w-0 pr-3">
                  <p className="text-sm text-mm-primary truncate font-medium">
                    {c.title}
                  </p>
                  <p className="text-xs text-mm-secondary mt-0.5">
                    {c.mode === "manage" ? "Center your mind" : "A listening ear"}
                    {" · "}
                    {formatRelative(c.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => handleDelete(c.chat_id, e)}
                  className="p-2 rounded-full opacity-0 group-hover:opacity-100 hover:bg-mm-alt transition-opacity"
                  data-testid={`delete-chat-${c.chat_id}`}
                  aria-label="Delete"
                >
                  <Trash2 size={15} className="text-mm-secondary" />
                </button>
              </li>
            ))}
          </ul>
        )}

        <p className="text-[11px] text-mm-secondary mt-12 leading-relaxed">
          MindManage is supportive guidance, not a medical service. In a crisis,
          please contact 988 (US), iCall +91 9152987821 (India), Samaritans 116 123 (UK), or local emergency services.
        </p>
      </div>
    </div>
  );
}
