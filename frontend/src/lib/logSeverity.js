const ERROR_RE = /\b(error|err|fatal|critical)\b/i
const WARNING_RE = /\b(warn|warning)\b/i

export function classifyLogLine(line) {
  const text = String(line ?? "")
  if (ERROR_RE.test(text)) return "error"
  if (WARNING_RE.test(text)) return "warning"
  return "default"
}
