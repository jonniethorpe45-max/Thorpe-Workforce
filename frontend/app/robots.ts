import type { MetadataRoute } from "next";
import { getPublicAppUrl } from "@/lib/runtimeConfig";

export default function robots(): MetadataRoute.Robots {
  const base = getPublicAppUrl();
  return {
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: `${base}/sitemap.xml`
  };
}
