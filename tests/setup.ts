import "@testing-library/jest-dom";
import { vi, beforeEach } from "vitest";
import { resetMockState } from "../src/services/mock";

// jsdom does not implement scrollIntoView (used by Jonathan chat)
Element.prototype.scrollIntoView = vi.fn();

beforeEach(() => {
  resetMockState();
});
