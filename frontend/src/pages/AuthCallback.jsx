import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api, tokenStore } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/token=([^&]+)/);
    const token = match ? decodeURIComponent(match[1]) : null;

    if (!token) {
      navigate("/", { replace: true });
      return;
    }

    tokenStore.set(token);
    // Clean URL fragment
    window.history.replaceState({}, "", "/home");

    api.me()
      .then((u) => {
        setUser(u);
        navigate("/home", { replace: true, state: { user: u } });
      })
      .catch(() => {
        tokenStore.clear();
        navigate("/", { replace: true });
      });
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-mm" data-testid="auth-callback">
      <p className="font-serif-mm italic text-mm-secondary mm-pulse">Preparing your space…</p>
    </div>
  );
}
