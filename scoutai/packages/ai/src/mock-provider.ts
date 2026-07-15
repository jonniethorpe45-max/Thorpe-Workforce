import type { AIProvider, AIRequest, AIResponse } from './types';

export class MockAIProvider implements AIProvider {
  private readonly defaultOutput: unknown;

  constructor(defaultOutput: unknown = { summary: 'mock response' }) {
    this.defaultOutput = defaultOutput;
  }

  async generateStructuredOutput<TOutput>(
    request: AIRequest<unknown>,
  ): Promise<AIResponse<TOutput>> {
    return {
      output: (request.metadata?.mockOutput
        ? JSON.parse(request.metadata.mockOutput)
        : this.defaultOutput) as TOutput,
      model: request.model ?? 'mock-model',
      usage: {
        inputTokens: request.prompt.length,
        outputTokens: 32,
      },
    };
  }
}
