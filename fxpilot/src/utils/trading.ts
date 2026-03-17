interface PositionSizeInput {
  accountBalance: number
  riskPercent: number
  stopLossPips: number
  pipValuePerUnit: number
  maxUnits?: number
}

export function calculatePositionSize(input: PositionSizeInput) {
  const riskCapital = input.accountBalance * (input.riskPercent / 100)
  const rawUnits = riskCapital / (input.stopLossPips * input.pipValuePerUnit)
  const boundedUnits = input.maxUnits ? Math.min(rawUnits, input.maxUnits) : rawUnits

  return Math.max(0, Math.floor(boundedUnits))
}

export function calculatePnL(params: {
  direction: 'BUY' | 'SELL'
  units: number
  openPrice: number
  currentPrice: number
}) {
  const delta =
    params.direction === 'BUY'
      ? params.currentPrice - params.openPrice
      : params.openPrice - params.currentPrice

  return Number((delta * params.units).toFixed(2))
}

export function calculateDrawdown(equitySeries: number[]) {
  if (equitySeries.length === 0) {
    return 0
  }

  let peak = equitySeries[0]
  let maxDrawdown = 0

  for (const value of equitySeries) {
    if (value > peak) {
      peak = value
    }
    const drawdown = ((peak - value) / peak) * 100
    maxDrawdown = Math.max(maxDrawdown, drawdown)
  }

  return Number(maxDrawdown.toFixed(2))
}
