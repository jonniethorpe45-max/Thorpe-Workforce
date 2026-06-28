export function getJonathanSourceLabel(source?: string): string {
  switch (source) {
    case "openai":
      return "Cloud AI";
    case "cloud_fallback":
      return "Cloud AI (local fallback)";
    case "cloud_unconfigured":
      return "Cloud AI not configured";
    default:
      return "Autonomous repair";
  }
}

export function isCloudAiActive(config: {
  enabled: boolean;
  api_key_configured: boolean;
}): boolean {
  return config.enabled && config.api_key_configured;
}
