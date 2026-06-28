/** Split text into word and whitespace tokens for progressive reveal. */
export function tokenizeForReveal(text: string): string[] {
  if (!text) return [];
  return text.match(/\S+|\s+/g) ?? [text];
}

export const DEFAULT_WORD_REVEAL_MS = 90;
