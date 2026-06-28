import { useEffect, useState } from "react";
import { CreditCard, Check, Zap, Building2 } from "lucide-react";
import { thorpeApi } from "../services/tauri";
import { useAppStore } from "../services/store";
import type { LicenseInfo } from "../services/types";

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
  },
];

export function LicensingPage() {
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [licenseKey, setLicenseKey] = useState("");
  const [activating, setActivating] = useState(false);
  const { setLicense: setStoreLicense, addNotification } = useAppStore();

  useEffect(() => {
    thorpeApi.getLicenseInfo().then((l) => {
      setLicense(l);
      setStoreLicense(l);
    });
  }, [setStoreLicense]);

  const activate = async () => {
    if (!licenseKey.trim()) return;
    setActivating(true);
    try {
      const result = await thorpeApi.activateLicense(licenseKey.trim());
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

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Licensing & Subscription</h1>
        <p className="mt-1 text-gray-400">
          Choose the plan that fits your needs. Payment integration coming soon.
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

      <div className="grid gap-6 lg:grid-cols-3">
        {PLANS.map((plan) => {
          const Icon = plan.icon;
          const isCurrent = license?.tier === plan.tier;
          return (
            <div
              key={plan.tier}
              className={`card relative ${
                plan.popular ? "border-thorpe-500/50 ring-1 ring-thorpe-500/20" : ""
              } ${isCurrent ? "bg-thorpe-600/5" : ""}`}
            >
              {plan.popular && (
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
              {isCurrent && (
                <p className="mt-4 text-center text-sm font-medium text-thorpe-400">Current Plan</p>
              )}
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
          <button onClick={activate} disabled={activating} className="btn-primary">
            {activating ? "Activating..." : "Activate"}
          </button>
        </div>
        <p className="text-xs text-gray-500">
          Payment integration (Stripe) is prepared as a placeholder for future release.
        </p>
      </div>
    </div>
  );
}
