import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import RestartMenu from "@/components/RestartMenu"

export default function ServiceActions({
  disabled,
  building,
  onStart,
  onStop,
  onRestart,
  onRestartSam,
  onBuild,
  onClean,
  onKillPorts,
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      <Button size="xs" disabled={disabled} onClick={onStart}>
        Start
      </Button>
      <Button size="xs" variant="outline" disabled={disabled} onClick={onStop}>
        Stop
      </Button>
      <RestartMenu disabled={disabled} onRestartAll={onRestart} onRestartSam={onRestartSam} />
      <Button size="xs" variant="outline" disabled={disabled} onClick={onBuild}>
        {building ? (
          <>
            <Spinner data-icon="inline-start" />
            Building…
          </>
        ) : (
          "Build"
        )}
      </Button>
      <Button size="xs" variant="destructive" disabled={disabled} onClick={onClean}>
        Clean
      </Button>
      <Button size="xs" variant="destructive" onClick={onKillPorts}>
        Kill Ports
      </Button>
    </div>
  )
}
