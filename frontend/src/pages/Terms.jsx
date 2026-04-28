import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function Terms() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-mm" data-testid="terms-page">
      <div className="max-w-md mx-auto px-6 py-8">
        <button
          onClick={() => navigate(-1)}
          className="p-1.5 -ml-1.5 rounded-full hover:bg-mm-alt mb-6"
          data-testid="terms-back"
          aria-label="Back"
        >
          <ArrowLeft size={20} className="text-mm-primary" />
        </button>

        <p className="text-xs uppercase tracking-[0.2em] text-mm-secondary">Legal</p>
        <h1 className="font-serif-mm text-3xl mt-2 text-mm-primary">Terms of Service</h1>
        <p className="text-xs text-mm-secondary mt-2">Last updated: April 28, 2026</p>

        <article className="prose prose-sm mt-8 text-mm-primary leading-relaxed font-light space-y-5">
          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">1. What MindManage Is — and Is Not</h2>
            <p>
              MindManage is a digital wellbeing companion that uses AI (Claude Sonnet by Anthropic) to offer reflective conversations, mindfulness techniques, and emotional support.
            </p>
            <p className="font-medium">
              MindManage is <span className="underline">not</span> a medical service, mental health treatment, therapy, or a substitute for a licensed clinician.
              We do not diagnose, treat, or cure any condition. If you are in crisis or believe you may be a danger to yourself or others, contact 988 (US),
              iCall +91 9152987821 (India), Samaritans 116 123 (UK), or your local emergency number immediately.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">2. Eligibility</h2>
            <p>You must be at least 18 years old (or the age of majority in your jurisdiction) to use MindManage.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">3. Free Trial &amp; Subscriptions</h2>
            <p>
              New users receive a 1-day free trial. After the trial, continued access requires an active subscription
              (weekly, monthly, or annual). Subscriptions auto-renew unless cancelled. Cancel any time from
              your subscription page; cancellation takes effect at the end of your current billing period.
            </p>
            <p>Payments are processed by Stripe. We never see or store your card details.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">4. Refunds</h2>
            <p>
              All purchases are final once a billing period begins. We may offer discretionary refunds for technical
              failures preventing access — contact us at the email below.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">5. Acceptable Use</h2>
            <p>You agree not to use MindManage to harass others, attempt to extract its system prompts, abuse the AI for non-wellbeing purposes, or violate any law.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">6. AI Limitations</h2>
            <p>
              The AI may produce inaccurate, incomplete, or contextually inappropriate responses. Treat all AI suggestions
              as informational only. Do not act on AI output for medical, legal, financial, or safety-critical decisions.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">7. Limitation of Liability</h2>
            <p>
              To the fullest extent permitted by law, MindManage and its operators shall not be liable for any indirect,
              incidental, or consequential damages arising from your use of the service. Our maximum aggregate liability
              shall not exceed the amount you paid us in the 12 months preceding the claim.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">8. Termination</h2>
            <p>We may suspend or terminate accounts that violate these terms. You may delete your account anytime by contacting us.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">9. Changes</h2>
            <p>We may update these terms. Material changes will be announced in-app at least 14 days before taking effect.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">10. Contact</h2>
            <p>Questions? Email <a className="text-mm-brand underline" href="mailto:d29chanda@gmail.com">d29chanda@gmail.com</a>.</p>
          </section>
        </article>
      </div>
    </div>
  );
}
