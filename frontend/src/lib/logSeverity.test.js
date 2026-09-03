import { describe, it, expect } from "vitest"
import { classifyLogLine } from "./logSeverity.js"

describe("classifyLogLine", () => {
  it("classifies error keywords", () => {
    expect(classifyLogLine("ERROR: boom")).toBe("error")
    expect(classifyLogLine("something err failed")).toBe("error")
    expect(classifyLogLine("FATAL")).toBe("error")
    expect(classifyLogLine("CRITICAL")).toBe("error")
  })

  it("classifies warning keywords", () => {
    expect(classifyLogLine("WARN disk low")).toBe("warning")
    expect(classifyLogLine("Warning: slow")).toBe("warning")
  })

  it("returns default for non-matching lines", () => {
    expect(classifyLogLine("info started")).toBe("default")
    expect(classifyLogLine("terror")).toBe("default")
  })

  it("prefers error when both error and warning keywords appear", () => {
    expect(classifyLogLine("error and warn together")).toBe("error")
  })
})
