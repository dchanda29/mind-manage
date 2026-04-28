import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { LogIn } from "lucide-react";

const BG_IMAGE =
  "https://static.prod-images.emergentagent.com/jobs/e35675a9-5ef3-4be0-8b93-e10a254e86b9/images/81a29c6ddfdee16b689063471d0d9a58d9410cf17f51b6b9a6b556a91a94f2bb.png";

export default function Login() {
  const [quote, setQuote] = useState(null);

  useEffect(() => {
    api.getWelcomeQuote().then(setQuote).catch(() => {});
  }, []);

  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/home";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen relative bg-mm overflow-hidden" data-testid="login-page">
      <img
        src={BG_IMAGE}
        alt=""
        className="absolute inset-0 w-full h-full object-cover opacity-90"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-[#FDFBF7] via-[#FDFBF7]/85 to-transparent" />

      <div className="relative z-10 max-w-md mx-auto min-h-screen flex flex-col px-7 pt-16 pb-10">
        <div className="mm-fadein">
          <p className="text-xs uppercase tracking-[0.22em] text-mm-secondary">
            MindManage
          </p>
          <h1 className="font-serif-mm text-4xl sm:text-5xl tracking-tight leading-[1.05] mt-4 text-mm-primary">
            A quiet place
            <br />
            <span className="italic text-mm-brand">for your mind.</span>
          </h1>
        </div>

        <div className="mt-auto mm-fadein">
          {quote && (
            <blockquote
              className="mm-card p-6 mb-6"
              data-testid="welcome-quote"
            >
              <p className="font-serif-mm italic text-lg leading-relaxed text-mm-primary">
                &ldquo;{quote.text}&rdquo;
              </p>
              <p className="mt-3 text-xs uppercase tracking-[0.18em] text-mm-secondary">
                — {quote.author}
              </p>
            </blockquote>
          )}

          <button
            onClick={handleLogin}
            data-testid="google-login-button"
            className="mm-btn-primary w-full"
          >
            <LogIn size={18} />
            Continue with Google
          </button>
          <p className="text-xs text-center text-mm-secondary mt-4 leading-relaxed">
            1 day free. Then weekly, monthly, or annual.
            <br />
            We are not a substitute for a clinician.
          </p>
          <div className="flex justify-center gap-4 mt-3 text-[11px] text-mm-secondary">
            <a href="/legal/terms" data-testid="login-terms-link" className="hover:text-mm-brand">Terms</a>
            <a href="/legal/privacy" data-testid="login-privacy-link" className="hover:text-mm-brand">Privacy</a>
          </div>
        </div>
      </div>
    </div>
  );
}
