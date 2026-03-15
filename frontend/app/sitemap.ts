import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
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
