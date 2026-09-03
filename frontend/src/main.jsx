import React from "react"
import ReactDOM from "react-dom/client"
import { ThemeProvider } from "next-themes"
import { TooltipProvider } from "@/components/ui/tooltip"
import ThemeFavicon from "@/components/ThemeFavicon.jsx"
import "./index.css"
import App from "./App.jsx"

ReactDOM.createRoot(document.getElementById("root")).render(
  <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
    <ThemeFavicon />
    <TooltipProvider>
      <App />
    </TooltipProvider>
  </ThemeProvider>
)
