import { ChevronDownIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ButtonGroup } from "@/components/ui/button-group"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function RestartMenu({ disabled, onRestartAll, onRestartSam }) {
  return (
    <ButtonGroup>
      <Button variant="outline" size="xs" disabled={disabled} onClick={onRestartAll}>
        Restart
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              variant="outline"
              size="icon-xs"
              disabled={disabled}
              aria-label="Restart options"
            />
          }
        >
          <ChevronDownIcon />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuGroup>
            <DropdownMenuItem onClick={onRestartAll}>
              Everything
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onRestartSam}>
              SAM only
            </DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </ButtonGroup>
  )
}
