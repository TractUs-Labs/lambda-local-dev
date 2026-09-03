import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"
import { ThemeProvider } from "next-themes"
import { TooltipProvider } from "@/components/ui/tooltip"
import App from "./App.jsx"
import ServiceCard from "./ServiceCard.jsx"

function renderApp() {
  return render(
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <TooltipProvider>
        <App />
      </TooltipProvider>
    </ThemeProvider>
  )
}

class MockWebSocket {
  constructor() {
    this.close = vi.fn()
  }
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
    })))

    vi.stubGlobal("fetch", vi.fn(async (url) => {
      if (url === "/api/services") {
        return { ok: true, json: async () => [] }
      }
      return { ok: true, json: async () => ({}) }
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("cycles through light, dark, and system", async () => {
    renderApp()

    const toggle = await screen.findByRole("button", { name: /theme: system/i })
    fireEvent.click(toggle)
    expect(toggle).toHaveTextContent("Theme: Light")

    fireEvent.click(toggle)
    expect(toggle).toHaveTextContent("Theme: Dark")

    fireEvent.click(toggle)
    expect(toggle).toHaveTextContent("Theme: System")
  })
})

describe("ServiceCard", () => {
  beforeEach(() => {
    vi.stubGlobal("WebSocket", MockWebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders status badge and start/stop actions", () => {
    render(
      <TooltipProvider>
        <ServiceCard
          service={{
            name: "email-bot",
            sam_port: 3001,
            proxy_port: 8080,
            status: "stopped",
            tunnel_url: null,
          }}
          onStart={() => {}}
          onStop={() => {}}
          onRestart={() => {}}
          onRestartSam={() => {}}
          onBuild={() => {}}
          onClean={() => {}}
          onKillPorts={() => {}}
          onFocus={() => {}}
        />
      </TooltipProvider>
    )

    expect(screen.getByText("email-bot")).toBeInTheDocument()
    expect(screen.getByText("stopped")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument()
  })
})
