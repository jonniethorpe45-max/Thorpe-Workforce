import type { MetadataRoute } from "next";
import { getPublicAppUrl } from "@/lib/runtimeConfig";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = getPublicAppUrl();
  const now = new Date();
  const routes = [
    "",
    "/pricing",
    "/marketplace",
    "/workers",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/acceptable-use",
    "/login",
    "/signup"
  ];
  return routes.map((route) => ({
    url: `${base}${route}`,
    lastModified: now
  }));
}
