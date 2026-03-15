import type { Metadata } from "next";

import PublicWorkersPage from "@/app/workers/page";

export const metadata: Metadata = {
  title: "Marketplace",
  description: "Discover featured AI workers in the Thorpe Workforce marketplace."
};

export default function MarketplacePublicPage() {
  return <PublicWorkersPage />;
}
