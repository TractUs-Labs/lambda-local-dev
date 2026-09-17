import { useEffect, useRef, useState } from "react"
import { Empty, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { classifyLogLine } from "@/lib/logSeverity"
import { cn } from "@/lib/utils"

const TABS = ["sam", "proxy", "tunnel", "build"]

const SEVERITY_CLASS = {
  error: "text-red-500",
  warning: "text-yellow-500",
  default: "text-muted-foreground",
}

function LogPane({ lines, tall, viewportRef }) {
  return (
    <ScrollArea
      viewportRef={viewportRef}
      className={cn(tall ? "h-[clamp(280px,calc(100vh-26rem),560px)]" : "h-45")}
    >
      {lines.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No output</EmptyTitle>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="p-3 font-mono text-xs whitespace-pre-wrap wrap-break-word">
          {lines.map((line, i) => (
            <div key={i} className={SEVERITY_CLASS[classifyLogLine(line)]}>
              {line}
            </div>
          ))}
        </div>
      )}
    </ScrollArea>
  )
}

export default function ProcessLogPanel({ name, tall = false }) {
  const [activeTab, setActiveTab] = useState("sam")
  const [logs, setLogs] = useState({ sam: [], proxy: [], tunnel: [], build: [] })
  const viewportRef = useRef(null)

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws"
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/logs/${name}`)
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      setLogs((prev) => {
        const tab = msg.process in prev ? msg.process : "sam"
        return { ...prev, [tab]: [...prev[tab].slice(-499), msg.line] }
      })
    }
    return () => ws.close()
  }, [name])

  useEffect(() => {
    const el = viewportRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs, activeTab])

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList variant="line" className="w-full">
        {TABS.map((tab) => (
          <TabsTrigger key={tab} value={tab}>
            {tab}
          </TabsTrigger>
        ))}
      </TabsList>
      {TABS.map((tab) => (
        <TabsContent key={tab} value={tab}>
          <LogPane lines={logs[tab]} tall={tall} viewportRef={viewportRef} />
        </TabsContent>
      ))}
    </Tabs>
  )
}
