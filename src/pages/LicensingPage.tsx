import { useCallback, useEffect, useRef, useState } from "react";
import { CreditCard, Check, ExternalLink, Loader2, Zap, Building2 } from "lucide-react";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { BillingConfig, LicenseInfo } from "../services/types";

const PLANS = [
  {
    tier: "free",
    name: "Free",
    price: "$0",
    icon: Zap,
    features: [
      "Jonathan AI (autonomous repair)",
      "Basic system scans",
      "Limited diagnostic reports",
      "Knowledge base access",
    ],
    purchasable: false,
  },
  {
    tier: "professional",
    name: "Professional",
    price: "$19/mo",
    icon: Check,
    features: [
      "Everything in Free",
      "Full diagnostics",
      "Repair Center",
      "PDF report exports",
      "Unlimited reports",
      "Cloud AI integration",
    ],
    popular: true,
    purchasable: true,
  },
  {
    tier: "enterprise",
    name: "Enterprise",
    price: "Custom",
    icon: Building2,
    features: [
      "Everything in Professional",
      "Technician Workspace",
      "Enterprise AI Console",
      "Intelligence Console (Senior Engineer)",
    ],
    purchasable: true,
  },
] as const;

const ENTERPRISE_CONTACT_URL = "https://thorpe.app/contact?plan=enterprise";

export function LicensingPage() {
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [billing, setBilling] = useState<BillingConfig | null>(null);
  const [licenseKey, setLicenseKey] = useState("");
  const [activating, setActivating] = useState(false);
  const [checkoutTier, setCheckoutTier] = useState<string | null>(null);
  const [pollingSessionId, setPollingSessionId] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);
  const { setLicense: setStoreLicense, addNotification } = useAppStore();

  const refreshLicense = useCallback(async () => {
    const info = await thorpeApi.getLicenseInfo();
    setLicense(info);
    setStoreLicense(info);
  }, [setStoreLicense]);

  useEffect(() => {
    refreshLicense();
    thorpeApi.getBillingConfig().then(setBilling).catch(() => setBilling(null));
  }, [refreshLicense]);

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
      }
    };
  }, []);

  const activate = async (key?: string) => {
    const value = (key ?? licenseKey).trim();
    if (!value) return;
    setActivating(true);
    try {
      const result = await thorpeApi.activateLicense(value);
      setLicense(result);
      setStoreLicense(result);
      setLicenseKey("");
      addNotification({
        type: "success",
        title: "License Activated",
        message: `Welcome to Thorpe ${result.tier_display}!`,
      });
    } catch (err) {
      addNotification({ type: "error", title: "Activation Failed", message: String(err) });
    } finally {
      setActivating(false);
    }
  };

  const startPolling = (sessionId: string) => {
    setPollingSessionId(sessionId);
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
    }
    pollRef.current = window.setInterval(async () => {
      try {
        const status = await thorpeApi.getCheckoutStatus(sessionId);
        if (status.status === "complete" && status.license_key) {
          if (pollRef.current) {
            window.clearInterval(pollRef.current);
            pollRef.current = null;
          }
          setPollingSessionId(null);
          await activate(status.license_key);
        }
      } catch {
        // keep polling until timeout/cancel
      }
    }, 3000);
    window.setTimeout(() => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
        setPollingSessionId(null);
      }
    }, 5 * 60 * 1000);
  };

  const subscribe = async (tier: string) => {
    if (tier === "enterprise" && !billing?.stripe_configured) {
      await thorpeApi.openExternalUrl(ENTERPRISE_CONTACT_URL);
      return;
    }

    setCheckoutTier(tier);
    try {
      const session = await thorpeApi.createBillingCheckout(tier);
      await thorpeApi.openExternalUrl(session.checkout_url);
      startPolling(session.session_id);
      addNotification({
        type: "info",
        title: "Checkout opened",
        message: "Complete payment in your browser. Thorpe will activate your license automatically.",
      });
    } catch (err) {
      addNotification({
        type: "error",
        title: "Checkout unavailable",
        message: String(err),
      });
    } finally {
      setCheckoutTier(null);
    }
  };

  const stripeReady = billing?.stripe_configured ?? false;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Licensing & Subscription</h1>
        <p className="mt-1 text-gray-400">
          Subscribe with Stripe or activate a license key from your organization.
        </p>
      </div>

      {license && (
        <div className="card flex items-center gap-4">
          <CreditCard className="h-8 w-8 text-thorpe-400" />
          <div>
            <p className="text-sm text-gray-400">Current Plan</p>
            <p className="text-xl font-bold text-white">{license.tier_display}</p>
            {license.organization && (
              <p className="text-sm text-gray-400">{license.organization}</p>
            )}
            {license.expires_at && (
              <p className="text-sm text-gray-400">
                {license.tier === "free" && license.tier_display.includes("expired")
                  ? `Expired ${new Date(license.expires_at).toLocaleDateString()}`
                  : `Renews ${new Date(license.expires_at).toLocaleDateString()}`}
              </p>
            )}
          </div>
        </div>
      )}

      {pollingSessionId && (
        <div className="card flex items-center gap-3 border-thorpe-500/30 bg-thorpe-600/5">
          <Loader2 className="h-5 w-5 animate-spin text-thorpe-400" />
          <p className="text-sm text-gray-300">
            Waiting for payment confirmation… keep this window open after completing checkout.
          </p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {PLANS.map((plan) => {
          const Icon = plan.icon;
          const isCurrent = license?.tier === plan.tier;
          const isCheckingOut = checkoutTier === plan.tier;
          return (
            <div
              key={plan.tier}
              className={`card relative ${
                "popular" in plan && plan.popular ? "border-thorpe-500/50 ring-1 ring-thorpe-500/20" : ""
              } ${isCurrent ? "bg-thorpe-600/5" : ""}`}
            >
              {"popular" in plan && plan.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-thorpe-600 px-3 py-0.5 text-xs font-medium text-white">
                  Popular
                </span>
              )}
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-lg bg-thorpe-600/20 p-2">
                  <Icon className="h-5 w-5 text-thorpe-400" />
                </div>
                <div>
                  <h3 className="font-bold text-white">{plan.name}</h3>
                  <p className="text-lg text-thorpe-400">{plan.price}</p>
                </div>
              </div>
              <ul className="space-y-2">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-green-400" />
                    {f}
                  </li>
                ))}
              </ul>
              {isCurrent ? (
                <p className="mt-4 text-center text-sm font-medium text-thorpe-400">Current Plan</p>
              ) : plan.purchasable ? (
                <button
                  onClick={() => subscribe(plan.tier)}
                  disabled={isCheckingOut || (!stripeReady && plan.tier === "professional")}
                  className="btn-primary mt-4 w-full text-sm"
                >
                  {isCheckingOut ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Opening checkout…
                    </>
                  ) : plan.tier === "enterprise" && !stripeReady ? (
                    <>
                      Contact sales <ExternalLink className="h-4 w-4" />
                    </>
                  ) : (
                    "Subscribe"
                  )}
                </button>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="card space-y-4">
        <h3 className="font-medium text-white">Activate License Key</h3>
        <p className="text-sm text-gray-400">
          Enter your license key to activate your subscription.
        </p>
        <div className="flex gap-3">
          <input
            className="input flex-1 font-mono"
            placeholder="PRO-XXXX-XXXX-XXXX-CCCC"
            value={licenseKey}
            onChange={(e) => setLicenseKey(e.target.value)}
          />
          <button onClick={() => activate()} disabled={activating} className="btn-primary">
            {activating ? "Activating..." : "Activate"}
          </button>
        </div>
        <p className="text-xs text-gray-500">
          {stripeReady
            ? "Stripe checkout is connected. Subscriptions issue a license key automatically after payment."
            : "Stripe checkout requires THORPE_BILLING_API_URL pointing at your license server with Stripe configured."}
        </p>
      </div>
    </div>
  );
}
