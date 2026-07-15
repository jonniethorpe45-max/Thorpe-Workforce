import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  // ScoutAI may live nested under another monorepo before extraction.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
