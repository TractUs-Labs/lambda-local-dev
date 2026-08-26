import React, { useState, useEffect, useCallback } from "react";
import { useTheme } from "next-themes";
import ServiceCard from "./ServiceCard.jsx";
import ServiceDetail from "./ServiceDetail.jsx";

const themeOrder = ["system", "light", "dark"];

export default function App() {
  const [services, setServices] = useState([]);
  const [focusedService, setFocusedService] = useState(null);
  const { theme, setTheme } = useTheme();

  const fetchServices = useCallback(async () => {
    try {
      const res = await fetch("/api/services");
      if (res.ok) setServices(await res.json());
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchServices();
    const id = setInterval(fetchServices, 3000);
    return () => clearInterval(id);
  }, [fetchServices]);

  const action = useCallback(async (name, endpoint) => {
    await fetch(`/api/services/${name}/${endpoint}`, { method: "POST" });
    fetchServices();
  }, [fetchServices]);

  const focusedSvc = focusedService ? services.find((s) => s.name === focusedService) : null;

  const running = services.filter((s) => s.status === "running").length;
  const building = services.filter((s) => s.status === "building").length;

  const cycleTheme = useCallback(() => {
    const currentTheme = themeOrder.includes(theme) ? theme : "system";
    const currentIndex = themeOrder.indexOf(currentTheme);
    const nextTheme = themeOrder[(currentIndex + 1) % themeOrder.length];
    setTheme(nextTheme);
  }, [theme, setTheme]);

  const summary = () => {
    if (services.length === 0) return null;
    const parts = [];
    if (running > 0) parts.push(<span key="r" className="count-running">{running} running</span>);
    if (building > 0) parts.push(<span key="b" className="count-building">{building} building</span>);
    if (parts.length === 0) return "all stopped";
    return parts.reduce((acc, el, i) => (i === 0 ? [el] : [...acc, " · ", el]), []);
  };

  if (focusedSvc) {
    return (
      <ServiceDetail
        service={focusedSvc}
        onBack={() => setFocusedService(null)}
        onStart={() => action(focusedSvc.name, "start")}
        onStop={() => action(focusedSvc.name, "stop")}
        onRestart={() => action(focusedSvc.name, "restart")}
        onBuild={() => action(focusedSvc.name, "build")}
        onClean={() => action(focusedSvc.name, "clean")}
        onKillPorts={() => action(focusedSvc.name, "kill-ports")}
      />
    );
  }

  const themeLabel = theme || "system";

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-title">
          <span className="app-title-mark">⬡</span>
          tract-us dev
        </div>
        <div className="app-header-right">
          <button type="button" className="theme-toggle" onClick={cycleTheme}>
            Theme: {themeLabel.charAt(0).toUpperCase() + themeLabel.slice(1)}
          </button>
          <div className="app-summary">{summary()}</div>
        </div>
      </header>
      <div className="service-grid">
        {services.map((svc) => (
          <ServiceCard
            key={svc.name}
            service={svc}
            onStart={() => action(svc.name, "start")}
            onStop={() => action(svc.name, "stop")}
            onRestart={() => action(svc.name, "restart")}
            onBuild={() => action(svc.name, "build")}
            onClean={() => action(svc.name, "clean")}
            onKillPorts={() => action(svc.name, "kill-ports")}
            onFocus={() => setFocusedService(svc.name)}
          />
        ))}
      </div>
    </div>
  );
}
