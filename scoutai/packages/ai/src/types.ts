export interface AIRequest<TSchema = unknown> {
  prompt: string;
  schema: TSchema;
  model?: string;
  temperature?: number;
  metadata?: Record<string, string>;
}

export interface AIResponse<TOutput = unknown> {
  output: TOutput;
  model: string;
  usage?: {
    inputTokens: number;
    outputTokens: number;
  };
}

export interface AIProvider {
  generateStructuredOutput<TOutput>(
    request: AIRequest<unknown>,
  ): Promise<AIResponse<TOutput>>;
}
