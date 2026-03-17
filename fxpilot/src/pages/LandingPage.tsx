import { motion } from 'framer-motion'
import { ArrowRight, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { PwaInstallButton } from '@/components/PwaInstallButton'
import { PwaInstallHelpDialog } from '@/components/PwaInstallHelpDialog'

const features = [
  {
    title: 'Multi-Agent AI Trading Brain',
    description: 'Technical, sentiment, and risk agents vote on each opportunity before execution.',
    icon: Sparkles,
  },
  {
    title: 'Live Broker Connectivity',
    description: 'Secure OANDA proxy edge functions keep your credentials server-side.',
    icon: TrendingUp,
  },
  {
    title: 'Built-In Guardrails',
    description: 'Daily loss limits, drawdown breakers, and configurable risk controls.',
    icon: ShieldAlert,
  },
]

const ldJson = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'FXPilot',
  applicationCategory: 'FinanceApplication',
  operatingSystem: 'Web',
  description: 'AI-powered forex trading dashboard with live and paper trading.',
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background px-4 py-12 text-foreground">
      <script type="application/ld+json">{JSON.stringify(ldJson)}</script>
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="rounded-2xl border border-border bg-card p-8 sm:p-12"
        >
          <p className="text-sm uppercase tracking-[0.2em] text-primary">AI Forex Execution Platform</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
            Trade smarter with FXPilot autopilot intelligence.
          </h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">
            FXPilot combines live market data, broker execution, and multi-agent AI consensus into one
            production-ready dashboard for active forex traders.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/auth">
                Get started <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/dashboard">View dashboard</Link>
            </Button>
            <PwaInstallButton />
            <PwaInstallHelpDialog />
          </div>
          <p className="mt-6 text-xs text-danger">
            Risk Disclaimer: Forex trading carries significant risk and may not be suitable for all investors.
            Past performance is not indicative of future results.
          </p>
        </motion.div>

        <section className="mt-8 grid gap-4 sm:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <Card key={feature.title}>
                <Icon className="h-5 w-5 text-primary" />
                <h2 className="mt-3 font-semibold">{feature.title}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{feature.description}</p>
              </Card>
            )
          })}
        </section>
      </div>
    </div>
  )
}
