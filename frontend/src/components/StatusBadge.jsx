import { Badge } from "@/components/ui/badge"

const variants = {
  running: "default",
  building: "secondary",
  stopped: "outline",
}

export default function StatusBadge({ status }) {
  const variant = variants[status] ?? "outline"
  return (
    <Badge variant={variant}>
      {status === "building" ? "building…" : status}
    </Badge>
  )
}
