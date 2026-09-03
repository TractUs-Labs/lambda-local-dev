import React, { useState, useEffect, useCallback } from "react"
import { useTheme } from "next-themes"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import ServiceCard from "./ServiceCard.jsx"
import ServiceDetail from "./ServiceDetail.jsx"

const themeOrder = ["system", "light", "dark"]

export default function App() {
  const [services, setServices] = useState([])
  const [focusedService, setFocusedService] = useState(null)
  const { theme, setTheme } = useTheme()

  const fetchServices = useCallback(async () => {
    try {
      const res = await fetch("/api/services")
      if (res.ok) setServices(await res.json())
    } catch (_) {}
  }, [])

  useEffect(() => {
    fetchServices()
    const id = setInterval(fetchServices, 3000)
    return () => clearInterval(id)
  }, [fetchServices])

  const action = useCallback(async (name, endpoint, query = "") => {
    const qs = query ? `?${query}` : ""
    await fetch(`/api/services/${name}/${endpoint}${qs}`, { method: "POST" })
    fetchServices()
  }, [fetchServices])

  const focusedSvc = focusedService ? services.find((s) => s.name === focusedService) : null

  const running = services.filter((s) => s.status === "running").length
  const building = services.filter((s) => s.status === "building").length

  const cycleTheme = useCallback(() => {
    const currentTheme = themeOrder.includes(theme) ? theme : "system"
    const currentIndex = themeOrder.indexOf(currentTheme)
    const nextTheme = themeOrder[(currentIndex + 1) % themeOrder.length]
    setTheme(nextTheme)
  }, [theme, setTheme])

  const summary = () => {
    if (services.length === 0) return null
    if (running === 0 && building === 0) {
      return <span className="text-muted-foreground">all stopped</span>
    }
    return (
      <div className="flex items-center gap-2">
        {running > 0 && <Badge>{running} running</Badge>}
        {building > 0 && <Badge variant="secondary">{building} building</Badge>}
      </div>
    )
  }

  if (focusedSvc) {
    return (
      <ServiceDetail
        service={focusedSvc}
        onBack={() => setFocusedService(null)}
        onStart={() => action(focusedSvc.name, "start")}
        onStop={() => action(focusedSvc.name, "stop")}
        onRestart={() => action(focusedSvc.name, "restart", "scope=all")}
        onRestartSam={() => action(focusedSvc.name, "restart", "scope=sam")}
        onBuild={() => action(focusedSvc.name, "build")}
        onClean={() => action(focusedSvc.name, "clean")}
        onKillPorts={() => action(focusedSvc.name, "kill-ports")}
      />
    )
  }

  const themeLabel = theme || "system"

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8">
      <header className="flex items-center justify-between gap-4">
        <h1 className="font-heading text-base font-medium">tract-us dev</h1>
        <div className="flex items-center gap-3">
          <Button type="button" variant="outline" size="sm" onClick={cycleTheme}>
            Theme: {themeLabel.charAt(0).toUpperCase() + themeLabel.slice(1)}
          </Button>
          {summary()}
        </div>
      </header>
      <Separator />
      <div className="grid gap-3 md:grid-cols-2">
        {services.map((svc) => (
          <ServiceCard
            key={svc.name}
            service={svc}
            onStart={() => action(svc.name, "start")}
            onStop={() => action(svc.name, "stop")}
            onRestart={() => action(svc.name, "restart", "scope=all")}
            onRestartSam={() => action(svc.name, "restart", "scope=sam")}
            onBuild={() => action(svc.name, "build")}
            onClean={() => action(svc.name, "clean")}
            onKillPorts={() => action(svc.name, "kill-ports")}
            onFocus={() => setFocusedService(svc.name)}
          />
        ))}
      </div>
    </div>
  )
}
