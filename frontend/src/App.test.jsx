import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
    vi.stubGlobal("fetch", vi.fn(async (url) => {
      if (url === "/api/services") {
        return { ok: true, json: async () => [] };
      }
      return { ok: true, json: async () => ({}) };
    }));
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
