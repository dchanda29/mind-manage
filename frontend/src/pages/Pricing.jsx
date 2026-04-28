import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { ArrowLeft, Check, Sparkles, Settings } from "lucide-react";

const COPY = {
  weekly: "Try the practice for a week.",
  monthly: "Build a real rhythm. Most popular.",
  annual: "Commit to yourself. Best value.",
};

export default function Pricing() {
  const navigate = useNavigate();
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState(null);
  const [sub, setSub] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    api.getPackages().then(setPackages).catch(() => {});
    api.getSubStatus().then(setSub).catch(() => {});
  }, []);

  const handleSelect = async (id) => {
    setLoading(id);
    setError(null);
    try {
      const origin = window.location.origin;
      const { url } = await api.createCheckout(id, origin);
      window.location.href = url;
    } catch (e) {
      setError("Couldn't start checkout. Try again in a moment.");
      setLoading(null);
    }
  };

  const handleManage = async () => {
    setPortalLoading(true);
    setError(null);
    try {
      const { url } = await api.openBillingPortal(window.location.origin + "/home");
      window.location.href = url;
    } catch (e) {
      setError("Couldn't open billing portal. Email d29chanda@gmail.com to manage your subscription.");
      setPortalLoading(false);
    }
  };

  const isActive = sub?.state === "active";

  return (
    <div className="min-h-screen bg-mm" data-testid="pricing-page">
      <div className="max-w-md mx-auto px-6 py-8">
        <button
          onClick={() => navigate("/home")}
          className="p-1.5 -ml-1.5 rounded-full hover:bg-mm-alt mb-6"
          data-testid="pricing-back"
          aria-label="Back"
        >
          <ArrowLeft size={20} className="text-mm-primary" />
        </button>

        <div className="mb-9 mm-fadein">
          <p className="text-xs uppercase tracking-[0.2em] text-mm-secondary">
            Continue your practice
          </p>
          <h1 className="font-serif-mm text-3xl mt-3 text-mm-primary leading-tight">
            Keep the space.<br />
            <span className="italic text-mm-brand">Keep showing up.</span>
          </h1>
        </div>

        {isActive && (
          <div className="mm-card p-5 mb-5 mm-fadein" data-testid="active-sub-card">
            <p className="text-xs uppercase tracking-[0.18em] text-mm-secondary">Current plan</p>
            <p className="font-serif-mm text-xl text-mm-primary capitalize mt-1">{sub.plan}</p>
            <p className="text-xs text-mm-secondary mt-1">
              Renews {sub.until ? new Date(sub.until).toLocaleDateString() : "—"}
            </p>
            <button
              onClick={handleManage}
              disabled={portalLoading}
              data-testid="manage-subscription-button"
              className="mm-btn-secondary mt-4 w-full disabled:opacity-60"
            >
              <Settings size={16} />
              {portalLoading ? "Opening..." : "Manage / cancel subscription"}
            </button>
          </div>
        )}

        <div className="space-y-4 mm-stagger">
          {packages.map((p) => {
            const isMonthly = p.id === "monthly";
            const isAnnual = p.id === "annual";
            const perMonth = isAnnual ? (p.amount / 12).toFixed(2) : null;
            return (
              <button
                key={p.id}
                onClick={() => handleSelect(p.id)}
                disabled={loading !== null}
                data-testid={`plan-${p.id}`}
                className={`w-full text-left mm-card p-6 transition-shadow hover:shadow-[0_8px_30px_rgba(45,40,42,0.08)] disabled:opacity-60 ${
                  isMonthly ? "ring-1 ring-[#8A7E94]" : ""
                }`}
              >
                {isMonthly && (
                  <div className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-mm-brand mb-2">
                    <Sparkles size={11} />
                    Recommended
                  </div>
                )}
                <div className="flex items-baseline justify-between">
                  <h3 className="font-serif-mm text-2xl text-mm-primary">{p.label}</h3>
                  <p className="font-serif-mm text-2xl text-mm-primary">
                    ${p.amount.toFixed(2)}
                    <span className="text-xs text-mm-secondary ml-1 font-sans">/{p.id === "weekly" ? "wk" : p.id === "monthly" ? "mo" : "yr"}</span>
                  </p>
                </div>
                <p className="text-sm text-mm-secondary mt-1.5">{COPY[p.id]}</p>
                {perMonth && (
                  <p className="text-xs text-mm-brand mt-2">~${perMonth} / month</p>
                )}
                <div className="mt-4 flex items-center gap-2 text-sm text-mm-primary">
                  <Check size={15} className="text-mm-brand" />
                  {loading === p.id ? "Opening checkout..." : "Continue"}
                </div>
              </button>
            );
          })}
        </div>

        {error && (
          <p className="text-xs text-[#8C5555] mt-4" data-testid="pricing-error">{error}</p>
        )}

        <p className="text-[11px] text-mm-secondary mt-10 leading-relaxed">
          Renews automatically. Cancel anytime through Stripe. Test mode — use card 4242 4242 4242 4242 with any future date.
        </p>
      </div>
    </div>
  );
}
