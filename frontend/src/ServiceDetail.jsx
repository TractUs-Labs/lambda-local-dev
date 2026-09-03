import { ArrowLeftIcon, CopyIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import ProcessLogPanel from "@/components/ProcessLogPanel"
import ServiceActions from "@/components/ServiceActions"
import StatusBadge from "@/components/StatusBadge"

export default function ServiceDetail({
  service,
  onBack,
  onStart,
  onStop,
  onRestart,
  onRestartSam,
  onBuild,
  onClean,
  onKillPorts,
}) {
  const { name, sam_port, proxy_port, status, tunnel_url } = service
  const disabled = status === "building"

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-6 py-8">
      <Button variant="ghost" size="sm" className="self-start" onClick={onBack}>
        <ArrowLeftIcon data-icon="inline-start" />
        All services
      </Button>

      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <h1 className="font-heading text-2xl font-medium tracking-tight">{name}</h1>
          <p className="font-mono text-sm text-muted-foreground">
            :{sam_port} → :{proxy_port}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {tunnel_url && (
        <div className="flex min-w-0 items-center gap-1">
          <Button
            variant="link"
            nativeButton={false}
            render={<a href={tunnel_url} target="_blank" rel="noreferrer" />}
            className="min-w-0 justify-start truncate px-0"
          >
            {tunnel_url}
          </Button>
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => navigator.clipboard.writeText(tunnel_url)}
                  aria-label="Copy tunnel URL"
                />
              }
            >
              <CopyIcon />
            </TooltipTrigger>
            <TooltipContent>Copy tunnel URL</TooltipContent>
          </Tooltip>
        </div>
      )}

      <ServiceActions
        disabled={disabled}
        building={status === "building"}
        onStart={onStart}
        onStop={onStop}
        onRestart={onRestart}
        onRestartSam={onRestartSam}
        onBuild={onBuild}
        onClean={onClean}
        onKillPorts={onKillPorts}
      />

      <ProcessLogPanel name={name} tall />
    </div>
  )
}
