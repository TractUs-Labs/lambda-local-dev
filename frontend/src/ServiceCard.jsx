import { CopyIcon, Maximize2Icon } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import ProcessLogPanel from "@/components/ProcessLogPanel"
import ServiceActions from "@/components/ServiceActions"
import StatusBadge from "@/components/StatusBadge"

export default function ServiceCard({
  service,
  onStart,
  onStop,
  onRestart,
  onRestartSam,
  onBuild,
  onClean,
  onKillPorts,
  onFocus,
}) {
  const { name, sam_port, proxy_port, status, tunnel_url } = service
  const disabled = status === "building"

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="min-w-0 truncate">{name}</CardTitle>
        <CardDescription>
          <span className="font-mono">:{sam_port} / :{proxy_port}</span>
        </CardDescription>
        <CardAction className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={onFocus}
                  aria-label="Open detail view"
                />
              }
            >
              <Maximize2Icon />
            </TooltipTrigger>
            <TooltipContent>Open detail view</TooltipContent>
          </Tooltip>
          <StatusBadge status={status} />
        </CardAction>
      </CardHeader>

      {tunnel_url && (
        <CardContent className="flex min-w-0 items-center gap-1">
          <Button
            variant="link"
            nativeButton={false}
            render={<a href={tunnel_url} target="_blank" rel="noreferrer" />}
            className="min-w-0 flex-1 justify-start truncate px-0"
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
        </CardContent>
      )}

      <CardContent>
        <ProcessLogPanel name={name} />
      </CardContent>

      <CardFooter className="flex-wrap">
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
      </CardFooter>
    </Card>
  )
}
