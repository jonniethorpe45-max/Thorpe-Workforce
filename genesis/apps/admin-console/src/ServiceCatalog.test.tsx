import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ServiceCatalog } from "@genesis/ui";

describe("ServiceCatalog", () => {
  it("renders services", () => {
    render(
      <ServiceCatalog
        services={[{ id: "api-gateway", name: "API Gateway", port: 7999, status: "active" }]}
      />
    );
    expect(screen.getByText("API Gateway")).toBeTruthy();
  });
});
