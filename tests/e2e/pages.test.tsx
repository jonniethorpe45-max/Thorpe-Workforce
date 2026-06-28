import { describe, it, expect } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import { ROUTES, renderApp, waitForAppReady } from "./helpers";

describe("E2E page render", () => {
  it.each(ROUTES)("renders $path", async ({ path, heading }) => {
    const { container } = renderApp(path);
    await waitForAppReady();
    await waitFor(
      () => {
        const main = container.querySelector("main") ?? container;
        expect(within(main as HTMLElement).getByRole("heading", { name: heading })).toBeTruthy();
      },
      { timeout: 10000 }
    );
  });
});
