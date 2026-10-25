param([int]$Port = 8765)

$taskPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$taskServer = Join-Path $PSScriptRoot 'serve_agenda_workspace.py'
if (Test-Path -LiteralPath $taskPython) {
    & $taskPython $taskServer --port $Port
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $taskServer --port $Port
} else {
    Write-Error 'Python is required. Install Python or use the bundled Codex runtime.'
    exit 1
}
