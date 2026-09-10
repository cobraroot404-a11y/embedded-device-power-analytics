import "@testing-library/jest-dom/vitest";

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// jsdom does not implement ResizeObserver, which Recharts' ResponsiveContainer
// requires to measure its host element.
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;
