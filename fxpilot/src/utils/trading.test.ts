import { describe, expect, it } from 'vitest'

import { calculatePnL, calculatePositionSize } from '@/utils/trading'

describe('calculatePositionSize', () => {
  it('returns bounded floor units from risk model', () => {
    const units = calculatePositionSize({
      accountBalance: 100_000,
      riskPercent: 1,
      stopLossPips: 20,
      pipValuePerUnit: 0.0001,
      maxUnits: 60_000,
    })

    expect(units).toBe(60_000)
  })

  it('returns 0 on invalid risk conditions', () => {
    const units = calculatePositionSize({
      accountBalance: 0,
      riskPercent: 1,
      stopLossPips: 10,
      pipValuePerUnit: 0.0001,
    })

    expect(units).toBe(0)
  })
})

describe('calculatePnL', () => {
  it('calculates long PnL', () => {
    expect(
      calculatePnL({
        direction: 'BUY',
        units: 10_000,
        openPrice: 1.1,
        currentPrice: 1.1025,
      }),
    ).toBe(25)
  })

  it('calculates short PnL', () => {
    expect(
      calculatePnL({
        direction: 'SELL',
        units: 10_000,
        openPrice: 1.1,
        currentPrice: 1.0975,
      }),
    ).toBe(25)
  })
})
