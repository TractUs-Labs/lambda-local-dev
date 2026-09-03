import { useEffect } from "react"
import { useTheme } from "next-themes"

const STROKE = {
  light: "#171717",
  dark: "#fafafa",
}

function faviconHref(stroke) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 20l6.5 -9"/><path d="M19 20c-6 0 -6 -16 -12 -16"/></svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

export default function ThemeFavicon() {
  const { resolvedTheme } = useTheme()

  useEffect(() => {
    if (!resolvedTheme) return

    const stroke = STROKE[resolvedTheme] ?? STROKE.light
    let link = document.querySelector("link[rel='icon']")
    if (!link) {
      link = document.createElement("link")
      link.rel = "icon"
      link.type = "image/svg+xml"
      document.head.appendChild(link)
    }
    link.href = faviconHref(stroke)
  }, [resolvedTheme])

  return null
}
