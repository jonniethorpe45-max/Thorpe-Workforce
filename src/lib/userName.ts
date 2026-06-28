const GENERIC_NAMES = new Set(["user", "guest", "admin", "administrator"]);

/** First token from display_name; skips generic placeholder names. */
export function extractFirstName(displayName: string | null | undefined): string | null {
  const trimmed = displayName?.trim();
  if (!trimmed) return null;

  const first = trimmed.split(/\s+/)[0];
  if (!first || GENERIC_NAMES.has(first.toLowerCase())) return null;

  return first;
}

export function withFirstName(base: string, firstName: string | null, suffix = ""): string {
  if (!firstName) return `${base}${suffix}`;
  return `${base}, ${firstName}${suffix}`;
}
