import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { Check, Loader } from "lucide-react";

const POLL_INTERVAL_MS = 2000;
const MAX_ATTEMPTS = 6;

export default function BillingSuccess() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("checking"); // checking | paid | failed | timeout
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    const url = new URL(window.location.href);
    const orderId = url.searchParams.get("order_id");
    if (!orderId) {
      navigate("/home", { replace: true });
      return;
    }

    let attempts = 0;
    let stopped = false;

    const poll = async () => {
      attempts += 1;
      try {
        const res = await api.getPaymentStatus(orderId);
        setMeta(res);
        if (res.payment_status === "paid" || res.payment_status === "captured") {
          setStatus("paid");
          return;
        }
        if (res.status === "expired") {
          setStatus("failed");
          return;
        }
      } catch {
        if (attempts >= MAX_ATTEMPTS) {
          setStatus("timeout");
          return;
        }
      }
      if (attempts >= MAX_ATTEMPTS) {
        setStatus("timeout");
        return;
      }
      if (!stopped) setTimeout(poll, POLL_INTERVAL_MS);
    };

    poll();
    return () => { stopped = true; };
  }, [navigate]);

  return (
    <div className="min-h-screen bg-mm flex items-center justify-center px-6" data-testid="billing-success">
      <div className="max-w-md w-full mm-card p-8 text-center mm-fadein">
        {status === "checking" && (
          <>
            <Loader size={28} className="mx-auto text-mm-brand mm-pulse" />
            <p className="font-serif-mm italic text-mm-secondary mt-4">
              Confirming your space...
            </p>
          </>
        )}
        {status === "paid" && (
          <>
            <div className="w-14 h-14 rounded-full bg-mm-alt flex items-center justify-center mx-auto">
              <Check size={26} className="text-mm-brand" />
            </div>
            <h1 className="font-serif-mm text-3xl mt-5 text-mm-primary">
              Your space is reserved.
            </h1>
            <p className="text-mm-secondary mt-3 leading-relaxed">
              Thank you for choosing yourself. {meta?.package_id && <>Your <span className="capitalize">{meta.package_id}</span> plan is active.</>}
            </p>
            <button
              onClick={() => navigate("/home")}
              data-testid="back-home-button"
              className="mm-btn-primary mt-7 w-full"
            >
              Continue
            </button>
          </>
        )}
        {(status === "failed" || status === "timeout") && (
          <>
            <h1 className="font-serif-mm text-2xl text-mm-primary">
              Hmm, something didn&rsquo;t go through.
            </h1>
            <p className="text-mm-secondary mt-3 leading-relaxed">
              Your card wasn&rsquo;t charged. Take a breath and try again whenever you&rsquo;re ready.
            </p>
            <button
              onClick={() => navigate("/pricing")}
              data-testid="retry-button"
              className="mm-btn-secondary mt-6 w-full"
            >
              Back to plans
            </button>
          </>
        )}
      </div>
    </div>
  );
}
