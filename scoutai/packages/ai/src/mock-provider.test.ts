import { describe, expect, it } from 'vitest';
import { MockAIProvider } from './mock-provider';

describe('MockAIProvider', () => {
  it('returns structured mock output', async () => {
    const provider = new MockAIProvider({ rating: 4 });
    const response = await provider.generateStructuredOutput({
      prompt: 'Analyze clip',
      schema: {},
    });
    expect(response.output).toEqual({ rating: 4 });
    expect(response.model).toBe('mock-model');
  });
});
