import Link from "next/link";

const tiers = [
  { name: "Starter", price: "$299/mo", features: ["1 AI Sales Worker", "2 active campaigns", "Manual approval flow"] },
  { name: "Growth", price: "$899/mo", features: ["5 workers", "Unlimited campaigns", "Priority support"] },
  { name: "Enterprise", price: "Custom", features: ["Custom integrations", "Advanced controls", "Dedicated CSM"] }
];

export default function PricingPage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-16">
      <h1 className="text-4xl font-semibold text-slate-900">Pricing</h1>
      <p className="mt-2 text-slate-600">Simple plans that scale with your AI workforce.</p>
      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {tiers.map((tier) => (
          <div key={tier.name} className="card p-6">
            <h2 className="text-xl font-semibold">{tier.name}</h2>
            <p className="mt-2 text-3xl font-bold">{tier.price}</p>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              {tier.features.map((feature) => (
                <li key={feature}>• {feature}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mt-8">
        <Link href="/signup" className="btn-primary">
          Launch Your First AI Worker
        </Link>
      </div>
    </main>
  );
}
