import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function Privacy() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-mm" data-testid="privacy-page">
      <div className="max-w-md mx-auto px-6 py-8">
        <button
          onClick={() => navigate(-1)}
          className="p-1.5 -ml-1.5 rounded-full hover:bg-mm-alt mb-6"
          data-testid="privacy-back"
          aria-label="Back"
        >
          <ArrowLeft size={20} className="text-mm-primary" />
        </button>

        <p className="text-xs uppercase tracking-[0.2em] text-mm-secondary">Legal</p>
        <h1 className="font-serif-mm text-3xl mt-2 text-mm-primary">Privacy Policy</h1>
        <p className="text-xs text-mm-secondary mt-2">Last updated: April 28, 2026</p>

        <article className="prose prose-sm mt-8 text-mm-primary leading-relaxed font-light space-y-5">
          <section>
            <p className="italic font-serif-mm text-mm-secondary">
              Your inner world is yours. We treat your data with the same care you bring to your wellbeing.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">1. What We Collect</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><span className="font-medium">Account info</span> — name, email, profile picture (from Google sign-in).</li>
              <li><span className="font-medium">Chat content</span> — your messages and the AI&rsquo;s replies, stored so you can return to them. Only the most recent 5 chats are retained.</li>
              <li><span className="font-medium">Subscription &amp; payment metadata</span> — plan, status, Stripe session IDs. We never see your card.</li>
              <li><span className="font-medium">Technical logs</span> — IP, browser, error traces (kept ≤30 days).</li>
            </ul>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">2. How We Use It</h2>
            <p>
              To provide the chat experience, remember your conversations across sessions, manage your subscription,
              detect crisis language so we can guide you to professional help, and keep the service running.
            </p>
            <p>We do <span className="underline">not</span> sell your data. We do not use your messages to train AI models.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">3. Who Sees It</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li><span className="font-medium">Anthropic</span> — your messages are sent to Claude to generate replies (per Anthropic&rsquo;s privacy terms).</li>
              <li><span className="font-medium">Stripe</span> — payment processing only.</li>
              <li><span className="font-medium">Google</span> — sign-in only (we don&rsquo;t share chat data with Google).</li>
              <li><span className="font-medium">Hosting providers</span> — encrypted storage.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">4. Crisis Detection</h2>
            <p>
              If our system detects keywords indicating self-harm or imminent danger, we replace the AI reply with a
              static, pre-written response listing professional helplines. This detection happens locally on our server;
              no third party is contacted automatically.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">5. Your Rights</h2>
            <p>
              You can request a copy of your data, ask us to delete your account, or correct your info at any time —
              email <a className="text-mm-brand underline" href="mailto:privacy@mindmanage.app">privacy@mindmanage.app</a>.
              EU/UK users have GDPR rights; California users have CCPA rights.
            </p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">6. Retention</h2>
            <p>Chats: rolling last 5 per user. Account data: until you delete. Payment records: 7 years (legal requirement).</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">7. Cookies</h2>
            <p>We set a single <code>session_token</code> cookie (httpOnly, secure) to keep you signed in. No tracking cookies.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">8. Children</h2>
            <p>MindManage is not for users under 18. We do not knowingly collect data from minors.</p>
          </section>

          <section>
            <h2 className="font-serif-mm text-xl text-mm-primary">9. Contact</h2>
            <p>Email <a className="text-mm-brand underline" href="mailto:privacy@mindmanage.app">privacy@mindmanage.app</a>.</p>
          </section>
        </article>
      </div>
    </div>
  );
}
