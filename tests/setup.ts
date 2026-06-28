import "@testing-library/jest-dom";
import { vi } from "vitest";

// jsdom does not implement scrollIntoView (used by Jonathan chat)
Element.prototype.scrollIntoView = vi.fn();
