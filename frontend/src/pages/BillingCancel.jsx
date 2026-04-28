import { useNavigate } from "react-router-dom";

export default function BillingCancel() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-mm flex items-center justify-center px-6" data-testid="billing-cancel">
      <div className="max-w-md w-full text-center mm-fadein">
        <h1 className="font-serif-mm text-3xl text-mm-primary leading-tight">
          Take your time.
        </h1>
        <p className="font-serif-mm italic text-mm-brand text-2xl mt-1">
          We&rsquo;re here when you&rsquo;re ready.
        </p>
        <p className="text-mm-secondary mt-5 leading-relaxed">
          No charge was made. You can come back to this page any time from the home screen.
        </p>
        <div className="mt-8 flex flex-col gap-3">
          <button
            onClick={() => navigate("/pricing")}
            data-testid="cancel-back-plans"
            className="mm-btn-primary w-full"
          >
            See plans again
          </button>
          <button
            onClick={() => navigate("/home")}
            data-testid="cancel-go-home"
            className="mm-btn-secondary w-full"
          >
            Back to home
          </button>
        </div>
      </div>
    </div>
  );
}
