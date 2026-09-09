import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Without vitest's `globals: true`, Testing Library's auto-cleanup (which
// hooks the global afterEach) never registers, so a component rendered in
// one test would still be in the DOM for the next. Do it explicitly.
afterEach(() => {
  cleanup();
});
