import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { ThemeProvider } from "next-themes";
import App from "./App.jsx";

function renderApp() {
  return render(
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <App />
    </ThemeProvider>
  );
}

describe("App theme toggle", () => {
  beforeEach(() => {
    vi.stubGlobal("matchMedia", vi.fn().mockImplementation(() => ({
      matches: false,
      media: "",
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })));

    vi.stubGlobal("fetch", vi.fn(async (url) => {
      if (url === "/api/services") {
        return { ok: true, json: async () => [] };
      }
      return { ok: true, json: async () => ({}) };
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("cycles through light, dark, and system", async () => {
    renderApp();

    const toggle = await screen.findByRole("button", { name: /theme: system/i });
    fireEvent.click(toggle);
    expect(toggle).toHaveTextContent("Theme: Light");

    fireEvent.click(toggle);
    expect(toggle).toHaveTextContent("Theme: Dark");

    fireEvent.click(toggle);
    expect(toggle).toHaveTextContent("Theme: System");
  });
});
